import re
import shlex
import traceback
import textwrap

import subprocess
from subprocess import Popen, PIPE

from asyncio import CancelledError

import twitchio
from twitchio import errors
from twitchio.ext import commands, pubsub

import custom_bot
import settings


class RCECog(commands.Cog):

    def __init__(self, bot: custom_bot.Bot):
        self.bot = bot

    @commands.Cog.event()
    async def event_message(self, message: twitchio.Message):
        if message.echo:
            return
        # print('RCECog: ', message.author.name, message.content)

    @commands.command(aliases=['cmd'])
    async def exec(self, ctx: commands.Context):
        # get channel broadcaster
        broadcaster = await self.bot._http.get_users(ids=[], logins=[ctx.channel.name])
        user_access_token_resultset = self.bot.database.fetch_user_access_token_from_id(self.bot.user_id)

        if ctx.message.content == "!exec --help":
            await ctx.send("""exec: !exec [whatever /bin/bash commands you want to mess with the streamer]: 
                           This will run (mostly) un-sanitised bash commands on the streamers machine. rm -rf for the win.""")

        # only broadcaster can run exec commands
        # TODO: allow mods to run exec commands
        elif int(ctx.author.id) == int(broadcaster[0]['id']) or int(ctx.author.id) == 125444292:
            # grab the arbitrary bash command(s) without the bot prefix
            if ctx.message.content[:5] == '!exec':
                cmd = re.sub(fr'^{self.bot._prefix}{ctx.command.name}', '', ctx.message.content).strip()
            else:
                for alias in ctx.command.aliases:
                    cmd = re.sub(fr'^{self.bot._prefix}{alias}', '', ctx.message.content).strip()

            # strip operators
            operators = ['>>', '>', '&&', '&', ';', '..']
            if any(value in cmd for value in operators):
                for operator in operators:
                    cmd = cmd.replace(operator, '')

            # attempt to run the command(s) in a subprocess
            # which must finish running the command within 5 seconds or the process will be killed.
            try:
                proc: subprocess = None
                if '|' in cmd:
                    """ if input has pipes split input and pass first stdout into second command stdin """
                    cmd1, cmd2 = [x.strip() for x in cmd.split('|')]
                    command1 = shlex.split(cmd1)
                    command2 = shlex.split(cmd2)
                    pass
                    if command1[0] in settings.CMD_ALLOW_LIST and command2[0] == 'grep':
                        proc1 = Popen(command1[:4], shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
                        proc = Popen(command2[:4], shell=False, stdin=proc1.stdout, stdout=PIPE, stderr=PIPE)
                        proc1.stdout.close()
                else:
                    """ if input has no pipes run the command """
                    command = shlex.split(cmd)
                    pass
                    if command[0] in settings.CMD_ALLOW_LIST:
                        proc = Popen(command, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)

                try:
                    """ see if the process ran and return responses """
                    if proc is not None:
                        stdout, stderr = proc.communicate(timeout=5)
                        if len(stdout.decode()) > 0:
                            """ post the stdout to chat """
                            stdout = f'stdout: {stdout.decode()}'
                            try:
                                await self.bot._http.post_chat_announcement(token=user_access_token_resultset['access_token'],
                                                                            broadcaster_id=str(broadcaster[0]['id']),
                                                                            moderator_id=self.bot.user_id,
                                                                            message=f"{textwrap.shorten(stdout, width=500)}",
                                                                            color="green")
                            except errors.AuthenticationError:
                                await ctx.channel.send(content=stdout)
                        if len(stderr.decode()) > 0:
                            """ post the stderr to chat """
                            stderr = f'stderr: {stderr.decode()}'
                            try:
                                await self.bot._http.post_chat_announcement(token=user_access_token_resultset['access_token'],
                                                                            broadcaster_id=str(broadcaster[0]['id']),
                                                                            moderator_id=self.bot.user_id,
                                                                            message=f"{textwrap.shorten(stderr, width=500)}",
                                                                            color="orange")
                            except errors.AuthenticationError:
                                await ctx.channel.send(content=stderr)

                    else:
                        """ post message to chat informing they tried to run a command that wasn't in the allow list """
                        error_msg = f'Nice try {ctx.author.display_name} but the command(s) in `{cmd}` are not in the allow list!'
                        try:
                            await self.bot._http.post_chat_announcement(token=user_access_token_resultset['access_token'],
                                                                        broadcaster_id=str(broadcaster[0]['id']),
                                                                        moderator_id=self.bot.user_id,
                                                                        message=f"{textwrap.shorten(error_msg, width=500)}",
                                                                        color="orange")
                        except errors.AuthenticationError:
                            await ctx.channel.send(content=error_msg)

                except TimeoutError:
                    await ctx.channel.send('TimeoutError occurred')
                except subprocess.TimeoutExpired:
                    """ post message to chat informing they tried to run a command that took too long to run """
                    error_msg = f'Nice try {ctx.author.display_name} but the command(s) in `{cmd}` took too long to run!'
                    try:
                        await self.bot._http.post_chat_announcement(token=user_access_token_resultset['access_token'],
                                                                    broadcaster_id=str(broadcaster[0]['id']),
                                                                    moderator_id=self.bot.user_id,
                                                                    message=f"{textwrap.shorten(error_msg, width=500)}",
                                                                    color="orange")
                    except errors.AuthenticationError:
                        await ctx.channel.send(content=error_msg)
                except CancelledError:
                    await ctx.channel.send('CancelledError occurred')
                finally:
                    if proc is not None:
                        proc.terminate()
                        # os.killpg(os.getpgid(proc.pid), signal.SIGTERM)  # nuclear option
            except RuntimeError:
                await ctx.channel.send('An exception occurred')

    async def killmyshell(self, broadcaster_id: int, author_login: str, event: pubsub.PubSubChannelPointsMessage):
        # get channel broadcaster
        broadcaster = await self.bot._http.get_users(ids=[str(broadcaster_id)], logins=[])
        broadcaster_access_token_resultset = self.bot.database.fetch_user_access_token_from_id(broadcaster[0]['id'])
        broadcaster_access_token = broadcaster_access_token_resultset['access_token']
        mod_access_token_resultset = self.bot.database.fetch_user_access_token_from_id(self.bot.user_id)
        mod_access_token = mod_access_token_resultset['access_token']

        cmd1 = "echo $(xwininfo -tree -root | grep qterminal | head -n 1)"
        proc_id = subprocess.check_output(cmd1, shell=True).decode().split(" ")[0].strip()
        if proc_id != "":
            try:
                cmd2 = f"xkill -id {proc_id}"
                result = subprocess.check_output(cmd2, shell=True)
                result = f"{author_login} just killed {broadcaster[0]['display_name']}'s shell. " \
                         + f"stdout: {result.decode()}"
                try:
                    await self.bot._http.update_reward_redemption_status(token=broadcaster_access_token,
                                                                         broadcaster_id=str(broadcaster[0]['id']),
                                                                         reward_id=event.id,
                                                                         custom_reward_id=event.reward.id,
                                                                         status=True)
                    print(f"{textwrap.shorten(result, width=500)}")
                    await self.bot._http.post_chat_announcement(token=mod_access_token,
                                                                broadcaster_id=str(broadcaster[0]['id']),
                                                                moderator_id=self.bot.user_id,
                                                                message=f"{textwrap.shorten(result, width=500)}",
                                                                color="green")
                except errors.AuthenticationError:
                    print(f"{textwrap.shorten(result, width=500)}")

            except Exception as err:
                print(f"something broke {type(err)}", traceback.format_exc())
        else:
            try:
                await self.bot._http.update_reward_redemption_status(token=broadcaster_access_token,
                                                                     broadcaster_id=str(broadcaster[0]['id']),
                                                                     reward_id=event.id,
                                                                     custom_reward_id=event.reward.id,
                                                                     status=False)
                print(f"Unlucky {author_login} but there are no terminals open to kill")
                await self.bot._http.post_chat_announcement(token=mod_access_token,
                                                            broadcaster_id=str(broadcaster[0]['id']),
                                                            moderator_id=self.bot.user_id,
                                                            message=f"Unlucky {author_login} there are no terminals open to kill; your channel points have been refunded",
                                                            color="purple")
            except errors.AuthenticationError:
                print(f"Unlucky {author_login} but there are no terminals open to kill")
