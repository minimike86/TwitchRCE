import traceback

from twitchio.ext import commands
import subprocess
from subprocess import Popen, PIPE
import textwrap
from asyncio import CancelledError
from twitchio.ext import pubsub

from bot import prefix
import settings
from twitch import Twitch


class RCECog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.pubsub = pubsub.PubSubPool(bot)

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
        if ctx.author.name == 'msec':
            # grab the arbitrary bash command
            cmd = ctx.message.content.replace(prefix + ctx.command.name, '').strip()
            for alias in ctx.command.aliases:
                cmd = cmd.replace(prefix + alias, '').strip()

            # attempt to run the command in a subprocess
            # which must finish running the command within 5 seconds or the process will be killed.
            try:
                if '|' in cmd:
                    cmd1, cmd2 = [x.strip() for x in cmd.split('|')]

                    # drop cmd chains
                    # whitelist cmds to run
                    # if cmd1 in list

                    proc1 = Popen(cmd1, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
                    proc = Popen(cmd2, shell=True, stdin=proc1.stdout, stdout=PIPE, stderr=PIPE)
                    proc1.stdout.close()
                else:
                    proc = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
                try:
                    stdout, stderr = proc.communicate(timeout=5)
                    # stdout
                    if len(stdout.decode()) > 0:
                        await Twitch(settings.BROADCASTER_ID).send_chat_announcement(
                            f"{textwrap.shorten(f'stdout: {stdout.decode()}', width=self.bot.character_limit)}", "green")
                    # stderr
                    if len(stderr.decode()) > 0:
                        await Twitch(settings.BROADCASTER_ID).send_chat_announcement(
                            f"{textwrap.shorten(f'stderr: {stderr.decode()}', width=self.bot.character_limit)}", "orange")
                except TimeoutError:
                    await ctx.send('TimeoutError occurred')
                except CancelledError:
                    await ctx.send('CancelledError occurred')
                finally:
                    proc.kill()
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
