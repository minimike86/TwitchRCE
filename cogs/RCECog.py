from twitchio.ext import commands
import subprocess
from subprocess import Popen, PIPE
import textwrap
import shlex
from threading import Timer
from asyncio import CancelledError
from bot import prefix


class RCECog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.event()
    async def event_message(self, message):
        if message.echo:
            return
        print('RCECog: ', message.content)

    @commands.command()
    async def exec(self, ctx: commands.Context):
        # only msec user can run exec commands
        if ctx.author.name == 'msec':
            # grab the arbitrary bash command
            cmd = ctx.message.content.replace(prefix + ctx.command.name, '').strip()
            # attempt to run the command in a subprocess
            # which must finish running the command within 5 seconds or the process will be killed.
            try:
                proc = Popen(shlex.split(cmd), shell=True, stdout=PIPE, stderr=PIPE)
                timer = Timer(5, proc.kill)
                try:
                    timer.start()
                    stdout, stderr = proc.communicate()
                    await ctx.send(f'stdout: {textwrap.shorten(stdout.decode(), width=492)}')
                except TimeoutError:
                    await ctx.send('TimeoutError occurred')
                except CancelledError:
                    await ctx.send('CancelledError occurred')
                finally:
                    timer.cancel()
            except RuntimeError:
                await ctx.send('An exception occurred')

    @commands.command()
    async def killmyshell(self, ctx: commands.Context):
        cmd1 = "echo $(xwininfo -tree -root | grep qterminal | head -n 1)"
        proc_id = subprocess.check_output(cmd1, shell=True).decode().split(" ")[0].strip()
        if proc_id != "":
            try:
                cmd2 = f"xkill -id {proc_id}"
                result = subprocess.check_output(cmd2, shell=True)
                result = f"{ctx.author.display_name} just killed {ctx.channel.name}\"s shell. " \
                         + f"stdout: {result.decode()}"
                await ctx.send(f"{textwrap.shorten(result, width=492)}")
            except:
                print("something broke")
        else:
            await ctx.send(f"Unlucky {ctx.author.display_name} but there are no terminals open to kill")


def prepare(bot: commands.Bot):
    bot.add_cog(RCECog(bot))
