import logging
import re
import shlex
import subprocess
import textwrap
import traceback
from asyncio import CancelledError
from subprocess import PIPE, Popen

import twitchio
from colorama import Fore, Style
from twitchio import Chatter, PartialChatter, PartialUser, User, errors
from twitchio.ext import commands, pubsub

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bot.msecbot.custom_bot import CustomBot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class RCECog(commands.Cog):

    def __init__(self, bot: "CustomBot"):
        self.bot = bot

    @commands.Cog.event()
    async def event_message(self, message: twitchio.Message):
        if message.echo:
            return
        logger.info("RCECog: ", message.author.name, message.content)

    @commands.command(aliases=["cmd"])
    async def exec(self, ctx: commands.Context):
        # get channel broadcaster
        broadcaster: User = (
            await self.bot.fetch_users(ids=[], names=[ctx.channel.name])
        )[0]

        if ctx.message.content == "!exec --help":
            await ctx.send(
                """exec: !exec [whatever /bin/bash commands you want to mess with the streamer]: 
                This will run (mostly) un-sanitised bash commands on the streamers machine. rm -rf for the win."""
            )

        # only broadcaster or bot can run exec commands
        elif ctx.author.id == broadcaster.id or ctx.author.id == self.bot.bot_user.id:
            # grab the arbitrary bash command(s) without the bot prefix
            cmd = None
            if ctx.message.content[:5] == "!exec":
                cmd = re.sub(
                    rf"^{self.bot.get_prefix(message=ctx.message)}{ctx.command.name}",
                    "",
                    ctx.message.content,
                ).strip()
            else:
                for alias in ctx.command.aliases:
                    cmd = re.sub(
                        rf"^{self.bot.get_prefix(message=ctx.message)}{alias}",
                        "",
                        ctx.message.content,
                    ).strip()

            # strip operators
            operators = [">>", ">", "&&", "&", ";", ".."]
            if any(value in cmd for value in operators):
                for operator in operators:
                    cmd = cmd.replace(operator, "")

            # attempt to run the command(s) in a subprocess
            # which must finish running the command within 5 seconds or the process will be killed.
            try:
                proc: subprocess = None
                if "|" in cmd:
                    """if input has pipes split input and pass first stdout into second command stdin"""
                    cmd1, cmd2 = [x.strip() for x in cmd.split("|")]
                    command1 = shlex.split(cmd1)
                    command2 = shlex.split(cmd2)
                    pass
                    if (
                        command1[0] in self.bot.config.CMD_ALLOW_LIST
                        and command2[0] == "grep"
                    ):
                        proc1 = Popen(
                            command1[:4],
                            shell=False,
                            stdin=PIPE,
                            stdout=PIPE,
                            stderr=PIPE,
                        )
                        proc = Popen(
                            command2[:4],
                            shell=False,
                            stdin=proc1.stdout,
                            stdout=PIPE,
                            stderr=PIPE,
                        )
                        proc1.stdout.close()
                else:
                    """if input has no pipes run the command"""
                    command = shlex.split(cmd)
                    pass
                    if command[0] in self.bot.config.CMD_ALLOW_LIST:
                        proc = Popen(
                            command, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE
                        )

                try:
                    """see if the process ran and return responses"""
                    if proc is not None:
                        stdout, stderr = proc.communicate(timeout=5)
                        if len(stdout.decode()) > 0:
                            """post the stdout to chat"""
                            stdout = f"stdout: {stdout.decode()}"
                            try:
                                await self.bot.post_chat_announcement(
                                    broadcaster=broadcaster,
                                    moderator=self.bot.bot_user,
                                    message=f"{textwrap.shorten(stdout, width=500)}",
                                    color="green",
                                )
                            except errors.AuthenticationError:
                                await ctx.channel.send(content=stdout)
                        if len(stderr.decode()) > 0:
                            """post the stderr to chat"""
                            stderr = f"stderr: {stderr.decode()}"
                            try:
                                await self.bot.post_chat_announcement(
                                    broadcaster=broadcaster,
                                    moderator=self.bot.bot_user,
                                    message=f"{textwrap.shorten(stderr, width=500)}",
                                    color="orange",
                                )
                            except errors.AuthenticationError:
                                await ctx.channel.send(content=stderr)

                    else:
                        """post message to chat informing they tried to run a command that wasn't in the allow list"""
                        # noinspection DuplicatedCode
                        error_msg = (
                            f"Nice try {ctx.author.display_name} but the command(s) in '{cmd}' "
                            f"are not in the allow list!"
                        )
                        try:
                            await self.bot.post_chat_announcement(
                                broadcaster=broadcaster,
                                moderator=self.bot.bot_user,
                                message=f"{textwrap.shorten(error_msg, width=500)}",
                                color="orange",
                            )
                        except errors.AuthenticationError:
                            await ctx.channel.send(content=error_msg)

                except TimeoutError:
                    await ctx.channel.send("TimeoutError occurred")
                except subprocess.TimeoutExpired:
                    """post message to chat informing they tried to run a command that took too long to run"""
                    # noinspection DuplicatedCode
                    error_msg = (
                        f"Nice try {ctx.author.display_name} but the command(s) in '{cmd}' "
                        f"took too long to run!"
                    )
                    try:
                        await self.bot.post_chat_announcement(
                            broadcaster=broadcaster,
                            moderator=self.bot.bot_user,
                            message=f"{textwrap.shorten(error_msg, width=500)}",
                            color="orange",
                        )
                    except errors.AuthenticationError:
                        await ctx.channel.send(content=error_msg)
                except CancelledError:
                    await ctx.channel.send("CancelledError occurred")
                finally:
                    if proc is not None:
                        proc.terminate()
                        # os.killpg(os.getpgid(proc.pid), signal.SIGTERM)  # nuclear option
            except RuntimeError:
                await ctx.channel.send("An exception occurred")

    async def kill_my_shell(
        self,
        broadcaster: User | PartialUser,
        chatter: Chatter | PartialChatter,
        event: pubsub.PubSubChannelPointsMessage,
    ):
        cmd1 = "echo $(xwininfo -tree -root | grep qterminal | head -n 1)"
        proc_id = (
            subprocess.check_output(cmd1, shell=True).decode().split(" ")[0].strip()
        )
        if proc_id != "":
            try:
                cmd2 = f"xkill -id {proc_id}"
                result = subprocess.check_output(cmd2, shell=True)
                result = (
                    f"{Fore.RED}{chatter.display_name} just killed {broadcaster.name}'s shell. "
                    + f"{Fore.MAGENTA}stdout: {result.decode()}{Style.RESET_ALL}"
                )
                try:
                    await self.bot.update_reward_redemption_status(
                        broadcaster=broadcaster,
                        reward_id=event.id,
                        custom_reward_id=event.reward.id,
                        status=True,
                    )
                    print(f"{textwrap.shorten(result, width=500)}")
                    await self.bot.post_chat_announcement(
                        broadcaster=broadcaster,
                        moderator=self.bot.bot_user,
                        message=f"{textwrap.shorten(result, width=500)}",
                        color="green",
                    )
                except errors.AuthenticationError:
                    print(f"{textwrap.shorten(result, width=500)}")

            except Exception as err:
                print(
                    f"{Fore.RED}something broke {type(err)}{Style.RESET_ALL}",
                    traceback.format_exc(),
                )
        else:
            try:
                await self.bot.update_reward_redemption_status(
                    broadcaster=broadcaster,
                    reward_id=event.id,
                    custom_reward_id=event.reward.id,
                    status=False,
                )
                print(
                    f"{Fore.RED}Unlucky {chatter.display_name} but there are no terminals open to kill{Style.RESET_ALL}"
                )
                message = (
                    f"Unlucky {chatter.display_name} there's no terminals open to kill so your channel points have "
                    f"been refunded"
                )
                await self.bot.post_chat_announcement(
                    broadcaster=broadcaster,
                    moderator=self.bot.bot_user,
                    message=message,
                    color="orange",
                )
            except errors.AuthenticationError:
                print(
                    f"{Fore.RED}Unlucky {chatter.display_name} but there are no terminals open to kill{Style.RESET_ALL}"
                )
