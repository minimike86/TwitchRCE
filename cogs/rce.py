import os
import signal
import traceback

from twitchio.ext import commands
import subprocess
from subprocess import Popen, PIPE
import textwrap
from asyncio import CancelledError
from twitchio.ext import pubsub
import re
import settings
from twitch import Twitch


class RCECog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.pubsub = pubsub.PubSubPool(bot)

        self.CMD_REGEX = r"^[a-zA-Z]+(?!=\s)"

        @bot.event()
        async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
            if event.reward.title == 'Kill My Shell':  # title=Kill My Shell
                print('RCECog pubsub_channel_points: ', event.id, event.reward, event.status, event.user, event.timestamp)
                await self.killmyshell(self, event)

    @commands.Cog.event()
    async def event_message(self, message):
        if message.echo:
            return
        print('RCECog: ', message.content)

    @commands.command(aliases=['cmd'])
    async def exec(self, ctx: commands.Context):
        # only msec user can run exec commands
        if int(ctx.author.id) == settings.BROADCASTER_ID:
            # grab the arbitrary bash command(s) without the bot prefix
            cmd = ctx.message.content.replace(self.bot.get_prefix() + ctx.command.name, '').strip()
            for alias in ctx.command.aliases:
                cmd = cmd.replace(self.bot.get_prefix() + alias, '').strip()

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
                            await Twitch(settings.BROADCASTER_ID).send_chat_announcement(
                                f"{textwrap.shorten(stdout, width=self.bot.character_limit)}", "green")
                        # stderr
                        if len(stderr.decode()) > 0:
                            stderr = f'stderr: {stderr.decode()}'
                            await Twitch(settings.BROADCASTER_ID).send_chat_announcement(
                                f"{textwrap.shorten(stderr, width=self.bot.character_limit)}", "orange")
                    else:
                        # cmd not in allow list
                        error_msg = f'Nice try but the command(s) in `{cmd}` are not in the allow list!'
                        await Twitch(settings.BROADCASTER_ID).send_chat_announcement(
                            f"{textwrap.shorten(error_msg, width=self.bot.character_limit)}", "orange")
                except TimeoutError:
                    await ctx.send('TimeoutError occurred')
                except CancelledError:
                    await ctx.send('CancelledError occurred')
                finally:
                    if proc is not None:
                        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except RuntimeError:
                await ctx.send('An exception occurred')

    @staticmethod
    async def killmyshell(self, event: pubsub.PubSubChannelPointsMessage):
        cmd1 = "echo $(xwininfo -tree -root | grep qterminal | head -n 1)"
        proc_id = subprocess.check_output(cmd1, shell=True).decode().split(" ")[0].strip()
        if proc_id != "":
            try:
                cmd2 = f"xkill -id {proc_id}"
                result = subprocess.check_output(cmd2, shell=True)
                result = f"{event.user.name} just killed MSec\'s shell. " \
                         + f"stdout: {result.decode()}"
                await Twitch(settings.BROADCASTER_ID).update_redemption_status(event.id, event.reward.id, True)
                print(f"{textwrap.shorten(result, width=self.bot.character_limit)}")
                await Twitch(settings.BROADCASTER_ID).send_chat_announcement(
                    f"{textwrap.shorten(result, width=self.bot.character_limit)}", "green")

            except Exception as err:
                print(f"something broke {type(err)}", traceback.format_exc())
        else:
            await Twitch(settings.BROADCASTER_ID).update_redemption_status(event.id, event.reward.id, False)
            print(f"Unlucky {event.user.name} but there are no terminals open to kill")
            await Twitch(settings.BROADCASTER_ID).send_chat_announcement(
                f"Unlucky {event.user.name} there are no terminals open to kill; your channel points have been refunded", "purple")


def prepare(bot: commands.Bot):
    bot.add_cog(RCECog(bot))
