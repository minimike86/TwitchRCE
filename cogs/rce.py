import re
import traceback
import textwrap

import subprocess
from subprocess import Popen, PIPE

from asyncio import CancelledError

import twitchio
from twitchio.ext import commands, pubsub

import settings


class RCECog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.CMD_REGEX = r"^[a-zA-Z]+(?!=\s)"

    @commands.Cog.event()
    async def event_message(self, message: twitchio.Message):
        if message.echo:
            return
        # print('RCECog: ', message.author.name, message.content)

    @commands.command(aliases=['cmd'])
    async def exec(self, ctx: commands.Context):
        if ctx.message.content == "!exec --help":
            await ctx.send("""exec: !exec [whatever /bin/bash commands you want to mess with the streamer]: 
                           This will run (mostly) un-sanitised bash commands on the streamers machine. rm -rf for the win.""")

        # only broadcaster can run exec commands
        elif int(ctx.author.id) == self.bot.user_id:
            # grab the arbitrary bash command(s) without the bot prefix
            cmd = ctx.message.content.replace(f"{self.bot._prefix}{ctx.command.name}", '').strip()
            for alias in ctx.command.aliases:
                cmd = cmd.replace(f"{self.bot._prefix}{alias}", '').strip()

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
                    cmd1, cmd2 = [x.strip() for x in cmd.split('|')]
                    command1 = re.match(self.CMD_REGEX, cmd1).group(0)
                    command2 = re.fullmatch(self.CMD_REGEX, cmd2)
                    if command1 in settings.CMD_ALLOW_LIST and command2 in settings.CMD_ALLOW_LIST:
                        proc1 = Popen(cmd1, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
                        proc = Popen(cmd2, shell=True, stdin=proc1.stdout, stdout=PIPE, stderr=PIPE)
                        proc1.stdout.close()
                else:
                    command = re.match(self.CMD_REGEX, cmd).group(0)
                    if command in settings.CMD_ALLOW_LIST:
                        proc = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
                try:
                    if proc is not None:
                        stdout, stderr = proc.communicate(timeout=5)
                        # stdout
                        if len(stdout.decode()) > 0:
                            stdout = f'stdout: {stdout.decode()}'
                            await ctx.channel.send(content=stdout)
                            # TODO: twitchio.errors.Unauthorized: You're not authorized to use this route.
                            # await self.bot._http.post_chat_announcement(token=settings.CHAT_OAUTH_ACCESS_TOKEN,
                            #                                             broadcaster_id=self.bot.user_id,
                            #                                             moderator_id='',
                            #                                             message=f"{textwrap.shorten(stdout, width=500)}",
                            #                                             color="green")

                        # stderr
                        if len(stderr.decode()) > 0:
                            stderr = f'stderr: {stderr.decode()}'
                            await ctx.send(content=stderr)
                            # TODO: twitchio.errors.Unauthorized: You're not authorized to use this route.
                            # await self.bot._http.post_chat_announcement(token=settings.CHAT_OAUTH_ACCESS_TOKEN,
                            #                                             broadcaster_id=self.bot.user_id,
                            #                                             moderator_id='',
                            #                                             message=f"{textwrap.shorten(stderr, width=500)}",
                            #                                             color="orange")

                    else:
                        # cmd not in allow list
                        error_msg = f'Nice try but the command(s) in `{cmd}` are not in the allow list!'
                        await ctx.send(content=error_msg)
                        # TODO: twitchio.errors.Unauthorized: You're not authorized to use this route.
                        # await self.bot._http.post_chat_announcement(token=settings.CHAT_OAUTH_ACCESS_TOKEN,
                        #                                             broadcaster_id=self.bot.user_id,
                        #                                             moderator_id='',
                        #                                             message=f"{textwrap.shorten(error_msg, width=500)}",
                        #                                             color="orange")

                except TimeoutError:
                    await ctx.send('TimeoutError occurred')
                except CancelledError:
                    await ctx.send('CancelledError occurred')
                finally:
                    pass
                    # if proc is not None:
                    #     os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except RuntimeError:
                await ctx.send('An exception occurred')

    async def killmyshell(self, event: pubsub.PubSubChannelPointsMessage):
        cmd1 = "echo $(xwininfo -tree -root | grep qterminal | head -n 1)"
        proc_id = subprocess.check_output(cmd1, shell=True).decode().split(" ")[0].strip()
        if proc_id != "":
            try:
                cmd2 = f"xkill -id {proc_id}"
                result = subprocess.check_output(cmd2, shell=True)
                result = f"{event.user.name} just killed my shell. " \
                         + f"stdout: {result.decode()}"
                await self.bot._http.update_reward_redemption_status(token=settings.USER_TOKEN,
                                                                     broadcaster_id=500,
                                                                     reward_id=event.id,
                                                                     custom_reward_id=event.reward.id,
                                                                     status=True)
                print(f"{textwrap.shorten(result, width=500)}")
                await self.bot._http.post_chat_announcement(token=settings.USER_TOKEN,
                                                            broadcaster_id=self.bot.user_id,
                                                            moderator_id='',
                                                            message=f"{textwrap.shorten(result, width=500)}",
                                                            color="green")

            except Exception as err:
                print(f"something broke {type(err)}", traceback.format_exc())
        else:
            await self.bot._http.update_reward_redemption_status(token=settings.USER_TOKEN,
                                                                 broadcaster_id=self.bot.user_id,
                                                                 reward_id=event.id,
                                                                 custom_reward_id=event.reward.id,
                                                                 status=False)
            print(f"Unlucky {event.user.name} but there are no terminals open to kill")
            await self.bot._http.post_chat_announcement(token=settings.USER_TOKEN,
                                                        broadcaster_id=self.bot.user_id,
                                                        moderator_id='',
                                                        message=f"Unlucky {event.user.name} there are no terminals open to kill; your channel points have been refunded",
                                                        color="purple")
