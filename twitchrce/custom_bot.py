import json
import random
import re
from typing import List, Optional

import twitchio
from colorama import Fore, Style
from twitchio import PartialUser, User
from twitchio.ext import commands, eventsub, pubsub

from twitchrce.api.virustotal.virus_total_api import VirusTotalApiClient
from twitchrce.config import settings


class Bot(commands.Bot):
    """Custom twitchio bot class"""

    def __init__(
        self,
        app_access_token: str,
        user_token: str,
        initial_channels: list[str],
        eventsub_public_url: str,
    ):
        super().__init__(
            prefix="!", token=user_token, initial_channels=initial_channels
        )

        self.app_access_token = app_access_token
        self.user_token = user_token

        self.psclient: pubsub.PubSubPool = pubsub.PubSubPool(client=self)
        self.esclient: eventsub.EventSubClient = eventsub.EventSubClient(
            client=self,
            webhook_secret="some_secret_string",
            callback_route=f"{eventsub_public_url}",
        )

        # TODO: Make persistent
        self.death_count = {}

        """ load commands from cogsss """
        from twitchrce.cogs.rce import RCECog

        self.add_cog(RCECog(self))

        from twitchrce.cogs.vip import VIPCog

        self.add_cog(VIPCog(self))

    async def update_bot_http_token(self, token):
        """updates the bots http client token"""
        super()._http.token = token

    async def __validate__(self, user_token: str):
        validate_result = await self._http.validate(token=user_token)
        print(f"{Fore.GREEN}Validation complete: {validate_result}{Style.RESET_ALL}")

    async def __psclient_init__(self, user_token: str, channel_id: int) -> None:
        topics = [
            pubsub.channel_points(user_token)[channel_id],
        ]
        await self.psclient.subscribe_topics(topics)
        print(
            f"{Fore.RED}Subscribing to psclient topics for "
            f"{Fore.MAGENTA}{channel_id}{Fore.RED}'s channel.{Style.RESET_ALL}"
        )

    async def __esclient_init__(self) -> None:
        await self.delete_all_event_subscriptions()

        """ start the esclient listening on specified port """
        try:
            self.loop.create_task(self.esclient.listen(port=80))
            print(
                f"{Fore.RED}Running EventSub server on "
                f"[{Fore.MAGENTA}port=80{Fore.RED}].{Style.RESET_ALL}"
            )
        except Exception as e:
            print(e.with_traceback(tb=None))

    async def subscribe_channel_events(self, broadcasters: List[User]):
        for broadcaster in broadcasters:
            print(
                f"{Fore.RED}Subscribing to esclient events for "
                f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
            )

            try:
                """create new event subscription for channel_follows event"""
                await self.esclient.subscribe_channel_follows_v2(
                    broadcaster=broadcaster.id, moderator=broadcaster.id
                )
                print(
                    f"{Fore.RED}Subscribed to {Fore.MAGENTA}channel_follows{Fore.RED} event for "
                    f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
                )
            except twitchio.HTTPException:
                print(
                    f"{Fore.RED}Failed to subscribe to {Fore.MAGENTA}channel_follows{Fore.RED} event for "
                    f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
                )

            try:
                """create new event subscription for channel_cheers event"""
                await self.esclient.subscribe_channel_cheers(broadcaster=broadcaster.id)
                print(
                    f"{Fore.RED}Subscribed to {Fore.MAGENTA}channel_cheers{Fore.RED} event for "
                    f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
                )
            except twitchio.HTTPException:
                print(
                    f"{Fore.RED}Failed to subscribe to {Fore.MAGENTA}channel_cheers{Fore.RED} event for "
                    f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
                )

            try:
                """create new event subscription for channel_subscriptions event"""
                await self.esclient.subscribe_channel_subscriptions(
                    broadcaster=broadcaster.id
                )
                print(
                    f"{Fore.RED}Subscribed to {Fore.MAGENTA}channel_subscriptions{Fore.RED} event for "
                    f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
                )
            except twitchio.HTTPException:
                print(
                    f"{Fore.RED}Failed to subscribe to {Fore.MAGENTA}channel_subscriptions{Fore.RED} event for "
                    f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
                )

            try:
                """create new event subscription for channel_raid event"""
                await self.esclient.subscribe_channel_raid(
                    to_broadcaster=broadcaster.id
                )
                print(
                    f"{Fore.RED}Subscribed to {Fore.MAGENTA}channel_raid{Fore.RED} event for "
                    f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
                )
            except twitchio.HTTPException:
                print(
                    f"{Fore.RED}Failed to subscribe to {Fore.MAGENTA}channel_raid{Fore.RED} event for "
                    f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
                )

            try:
                """create new event subscription for channel_stream_start event"""
                await self.esclient.subscribe_channel_stream_start(
                    broadcaster=broadcaster.id
                )
                print(
                    f"{Fore.RED}Subscribed to {Fore.MAGENTA}channel_stream_start{Fore.RED} event for {Fore.MAGENTA}"
                    f"{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
                )
            except twitchio.HTTPException:
                print(
                    f"{Fore.RED}Failed to subscribe to {Fore.MAGENTA}channel_stream_start{Fore.RED} event for "
                    f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
                )

            try:
                """create new event subscription for channel_stream_end event"""
                await self.esclient.subscribe_channel_stream_end(
                    broadcaster=broadcaster.id
                )
                print(
                    f"{Fore.RED}Subscribed to {Fore.MAGENTA}channel_stream_end{Fore.RED} event for {Fore.MAGENTA}"
                    f"{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
                )
            except twitchio.HTTPException:
                print(
                    f"{Fore.RED}Failed to subscribe to {Fore.MAGENTA}channel_stream_end{Fore.RED} event for "
                    f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
                )

            try:
                """create new event subscription for channel_charity_donate event"""
                await self.esclient.subscribe_channel_charity_donate(
                    broadcaster=broadcaster.id
                )
                print(
                    f"{Fore.RED}Subscribed to {Fore.MAGENTA}channel_charity_donate{Fore.RED} event for {Fore.MAGENTA}"
                    f"{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
                )
            except twitchio.HTTPException:
                print(
                    f"{Fore.RED}Failed to subscribe to {Fore.MAGENTA}channel_stream_end{Fore.RED} event for "
                    f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
                )

    async def delete_all_event_subscriptions(self):
        """before registering new event subscriptions remove old event subs"""
        app_token = self.app_access_token
        self.esclient.client._http.token = app_token
        self.esclient._http.__init__(client=self.esclient, token=app_token)
        es_subs = await self.esclient._http.get_subscriptions()
        print(
            f"{Fore.RED}Found {Fore.MAGENTA}{len(es_subs)}{Fore.RED} event subscription(s).{Style.RESET_ALL}"
        )
        for es_sub in es_subs:
            await self.esclient._http.delete_subscription(es_sub)
            print(
                f"{Fore.RED}Deleting the event subscription with id: "
                f"{Fore.MAGENTA}{es_sub.id}{Fore.RED}.{Style.RESET_ALL}"
            )

    async def delete_event_subscriptions(self, broadcasters: List[User]):
        """before registering new event subscriptions remove old event subs"""
        self.esclient._http.__init__(client=self.esclient, token=self.app_access_token)
        es_subs = await self.esclient._http.get_subscriptions()
        print(
            f"{Fore.RED}Found {Fore.MAGENTA}{len(es_subs)}{Fore.RED} event subscription(s).{Style.RESET_ALL}"
        )
        for es_sub in es_subs:
            if (
                "broadcaster_user_id" in es_sub.condition
                and int(es_sub.condition["broadcaster_user_id"]) == broadcasters[0].id
            ) or (
                "to_broadcaster_user_id" in es_sub.condition
                and int(es_sub.condition["to_broadcaster_user_id"])
                == broadcasters[0].id
            ):
                await self.esclient._http.delete_subscription(es_sub)
                print(
                    f"{Fore.RED}Deleting the event subscription with id: "
                    f"{Fore.MAGENTA}{es_sub.id}{Fore.RED} for channel "
                    f"{Fore.MAGENTA}{broadcasters[0].name}{Fore.RED}.{Style.RESET_ALL}"
                )

    async def set_stream_marker(
        self, payload: eventsub.NotificationEvent, event_string: str
    ):
        # create stream marker (Stream markers cannot be created when the channel is offline)
        if hasattr(payload.data, "reciever"):
            streams = await self._http.get_streams(user_ids=[payload.data.reciever.id])
        else:
            streams = await self._http.get_streams(
                user_ids=[payload.data.broadcaster.id]
            )

        if len(streams) >= 1 and streams[0]["type"] == "live":

            # Create the marker
            if hasattr(payload.data, "reciever"):
                await payload.data.reciever.create_marker(
                    token=self.user_token, description=event_string
                )
            else:
                await payload.data.broadcaster.create_marker(
                    token=self.user_token, description=event_string
                )

    @staticmethod
    async def detect_bot_spam(message: twitchio.Message) -> bool:
        if (
            str(message.content).count("offer promotion of your channel") >= 1
            or str(message.content)
            .lower()
            .count("viewers, followers, views, chat bots")
            >= 1
            or str(message.content)
            .lower()
            .count("The price is lower than any competitor")
            >= 1
            or str(message.content)
            .lower()
            .count("the quality is guaranteed to be the best")
            >= 1
            or str(message.content).lower().count("incredibly flexible and convenient")
            >= 1
            or str(message.content).lower().count("order management panel") >= 1
        ) and str(message.content).lower().count("dogehype") >= 1:
            print("Bot detected")
            return True
        return False

    async def event_ready(self):
        if len(self.connected_channels) == 0:
            """Bot failed to join channel."""
            await self.join_channels(channels=[settings.BOT_JOIN_CHANNEL])

        if len(self.connected_channels) >= 1:
            """Bot is logged into IRC and ready to do its thing."""
            # logins = [channel.name for channel in self.connected_channels]
            # user_data = await self._http.get_users(token=self._http.app_token, ids=[], logins=logins)
            for channel in self.connected_channels:
                print(
                    f"{Fore.BLUE}[BOT READY] Logged into channel(s): {Fore.MAGENTA}{channel.name}{Fore.BLUE}, "
                    f"as bot user: {Fore.MAGENTA}{self.nick}{Fore.BLUE} "
                    f"({Fore.MAGENTA}ID: {self.user_id}{Fore.BLUE})!{Style.RESET_ALL}"
                )
                # uncomment below to say in chat when the bot joins
                # await channel.send(f'Logged into channel(s): {channel.name}, as bot user: '
                #                    f'{self.nick} (ID: {self.user_id})')

            # By default, turn on the sound and user commands
            from cogs.ascii_cog import AsciiCog

            self.add_cog(AsciiCog(self))

    async def event_message(self, message: twitchio.Message):
        """Messages with echo set to True are messages sent by the bot. ignore them."""
        if message.echo:
            return
        # Print the contents of our message to console...
        print(
            f"{Fore.RED}[{message.channel.name}]{Fore.BLUE}[{message.author.name}]{Fore.RED}: {Fore.WHITE}"
            f"{message.content}{Style.RESET_ALL}"
        )

        """ Messages that include common bot spammer phrases auto-ban. """
        is_bot = await self.detect_bot_spam(message=message)
        if is_bot:
            user: PartialUser = await message.channel.user()
            # oauth user access token with the ``moderator:manage:banned_users`` scope
            await user.ban_user(
                token=self.user_token,
                moderator_id=user.id,
                user_id=int(message.author.id),
                reason="Banned for posting known bot spam/scam messages (eg: buy follows at dogehype)",
            )
        else:
            """Handle commands overriding the default `event_message`."""
            await self.handle_commands(message)

    async def add_kill_my_shell_redemption_reward(self, broadcaster: PartialUser):
        """
        Adds channel point redemption that immediately closes the last terminal window that was opened without warning
        """
        channel = await self._http.get_channels(broadcaster_id=broadcaster.id)
        if channel[0]["game_id"] is not None and int(channel[0]["game_id"]) in [
            509670,
            1469308723,
        ]:
            # 509670 = Science & Technology, 1469308723 = Software and Game Dev
            await self._http.create_reward(
                broadcaster_id=broadcaster.id,
                title="Kill My Shell",
                cost=6666,
                prompt="Immediately closes the last terminal window "
                "that was opened without warning!",
                global_cooldown=5 * 60,
                token=self.user_token,
            )
            print(
                f"{Fore.RED}Added {Fore.MAGENTA}`Kill My Shell`{Fore.RED} channel point redemption.{Style.RESET_ALL}"
            )

    async def add_vip_auto_redemption_reward(self, broadcaster: PartialUser):
        """Adds channel point redemption that adds the user to the VIP list automatically"""
        vips = await self._http.get_channel_vips(
            token=self.user_token, broadcaster_id=broadcaster.id, first=100
        )
        if len(vips) < settings.MAX_VIP_SLOTS:
            await self._http.create_reward(
                broadcaster_id=broadcaster.id,
                title="VIP",
                cost=80085,
                prompt="VIPs have the ability to equip a special chat "
                "badge and bypass the chat limit in slow mode!",
                max_per_user=1,
                global_cooldown=5 * 60,
                token=self.user_token,
            )
            print(
                f"{Fore.RED}Added {Fore.MAGENTA}`VIP`{Fore.RED} channel point redemption.{Style.RESET_ALL}"
            )

    async def delete_all_custom_rewards(self, broadcaster: PartialUser):
        """deletes all custom rewards (API limits deletes to those created by the bot)
        Requires a user access token that includes the channel:manage:redemptions scope.
        """
        rewards = await self._http.get_rewards(
            broadcaster_id=broadcaster.id, only_manageable=True, token=self.user_token
        )
        print(
            f"{Fore.RED}Got rewards: [{Fore.MAGENTA}{json.dumps(rewards)}{Fore.RED}]{Style.RESET_ALL}"
        )
        if rewards is not None:
            custom_reward_titles = ["Kill My Shell", "VIP"]
            for reward in list(
                filter(lambda x: x["title"] in custom_reward_titles, rewards)
            ):
                await self._http.delete_custom_reward(
                    broadcaster_id=broadcaster.id,
                    reward_id=reward["id"],
                    token=self.user_token,
                )
                print(
                    f"{Fore.RED}Deleted reward: [{Fore.MAGENTA}id={reward['id']}{Fore.RED}]"
                    f"[{Fore.MAGENTA}title={reward['title']}{Fore.RED}]{Style.RESET_ALL}"
                )

    async def announce_shoutout(
        self,
        ctx: Optional[commands.Context],
        broadcaster: PartialUser,
        channel: any,
        color: str,
    ):
        message: list[str] = [f"Please check out "]
        flattering_strings = [
            "the brilliant",
            "the amazing",
            "the outstanding",
            "the remarkable",
            "the exceptional",
            "the impressive",
            "the phenomenal",
            "the talented",
            "the genius",
            "the masterful",
        ]
        message.append(random.choice(flattering_strings))
        message.append(
            f" {channel['broadcaster_name']}'s channel over at "
            f"(https://www.twitch.tv/{channel['broadcaster_login']})!"
        )
        if not channel["game_name"] == "":
            message.append(f" They were last playing `{channel['game_name']}`.")

        error_count = 0
        try:
            await self.post_chat_announcement(
                token=self.user_token,
                broadcaster_id=broadcaster.id,
                message="".join(message),
                moderator_id=broadcaster.id,
                # Moderator ID must match the user ID in the user access token.
                color=color,
            )

        except Exception as error:
            print(
                f"{Fore.RED}Could not send shoutout announcement to {Fore.MAGENTA}{channel['broadcaster_name']}"
                f"{Fore.RED} from channel {Fore.MAGENTA}{broadcaster.name}{Fore.RED}: {error}{Style.RESET_ALL}"
            )
            error_count += 1
            raise

        try:
            """Perform a Twitch Shoutout command (https://help.twitch.tv/s/article/shoutouts?language=en_US).
            The channel giving a Shoutout must be live AND you cannot shoutout the current streamer.
            """
            if channel["broadcaster_id"] != str(broadcaster.id):
                streams = await self._http.get_streams(user_ids=[broadcaster.id])
                if len(streams) >= 1 and streams[0]["type"] == "live":
                    # Moderator ID must match the user ID in the user access token.
                    await self.broadcaster_shoutout(
                        broadcaster=broadcaster,
                        token=self.user_token,
                        to_broadcaster_id=channel["broadcaster_id"],
                        moderator_id=channel["broadcaster_id"],
                    )

        except Exception as error:
            """Eg: shoutout global cooldown "You have to wait 1m 30s before giving another Shoutout."""
            print(
                f"{Fore.RED}Could not perform a Twitch Shoutout command to {Fore.MAGENTA}{channel['broadcaster_name']}"
                f"{Fore.RED} from channel {Fore.MAGENTA}{broadcaster.name}{Fore.RED}: {error}{Style.RESET_ALL}"
            )
            raise

        if error_count >= 1:
            if ctx is not None:
                await ctx.send("".join(message))
            elif broadcaster is not None and hasattr(broadcaster.channel, "send"):
                await broadcaster.channel.send("".join(message))

    async def post_chat_announcement(
        self,
        token: str,
        broadcaster_id: str,
        message: str,
        moderator_id: str,
        color: str,
    ):
        """Post a shoutout announcement to chat; color = blue, green, orange, purple, or primary"""
        await self._http.post_chat_announcement(
            token=token,
            broadcaster_id=broadcaster_id,
            message=message,
            moderator_id=moderator_id,
            color=color,
        )

    async def broadcaster_shoutout(
        self,
        broadcaster: PartialUser | User,
        token: str,
        to_broadcaster_id: int,
        moderator_id: int,
    ):
        await broadcaster.shoutout(
            token=token, to_broadcaster_id=to_broadcaster_id, moderator_id=moderator_id
        )

    """
    COG COMMANDS BELOW ↓ ↓ ↓ ↓ ↓
    """

    @commands.command(aliases=["enablesounds"])
    async def soundson(self, ctx: commands.Context):
        from cogs.sounds_cog import SoundsCog

        self.add_cog(SoundsCog(self))

    @commands.command(aliases=["disablesounds"])
    async def soundsoff(self, ctx: commands.Context):
        from cogs.sounds_cog import SoundsCog

        self.remove_cog(SoundsCog(self).name)

    @commands.command(aliases=["enableusercommands"])
    async def usercommandson(self, ctx: commands.Context):
        from cogs.user_cog import UserCog

        self.add_cog(UserCog(self))

    @commands.command(aliases=["disableusercommands"])
    async def usercommandsoff(self, ctx: commands.Context):
        from cogs.user_cog import UserCog

        self.remove_cog(UserCog(self).name)

    """
    BOT COMMANDS BELOW ↓ ↓ ↓ ↓ ↓
    """

    @commands.command(aliases=["hi"])
    async def hello(self, ctx: commands.Context):
        """type !hello to say hello to author"""
        await ctx.send(f"Hello {ctx.author.name}!")

    @commands.command()
    async def join(self, ctx: commands.Context):
        """type !join <channel> to join the channel"""
        param_username = re.sub(
            r"^@", "", str(ctx.message.content).split(maxsplit=1)[1]
        )
        # Limit to broadcaster
        if ctx.author.is_broadcaster or int(ctx.author.id) == 125444292:
            await self.join_channels([param_username])

    @commands.command()
    async def leave(self, ctx: commands.Context):
        """type !leave <channel> to join the channel"""
        param_username = re.sub(
            r"^@", "", str(ctx.message.content).split(maxsplit=1)[1]
        )
        # Limit to broadcaster
        if (
            ctx.author.is_broadcaster
            or int(ctx.author.id) == 125444292
            and str(settings.BOT_JOIN_CHANNEL).lower() != param_username.lower()
        ):  # stay connected to init channel
            await self.part_channels([param_username])
            # also remove event subs
            broadcasters: List[User] = await self.fetch_users(names=[param_username])
            await self.delete_event_subscriptions(broadcasters=broadcasters)
        print(
            f"{Fore.RED}Connected_channels: {Fore.MAGENTA}{self.connected_channels}{Fore.RED}!{Style.RESET_ALL}"
        )

    @commands.command(aliases=["infosecstreams", "cyber_streams", "streams"])
    async def infosec_streams(self, ctx: commands.Context):
        """type !streams to drop a link to infosecstreams.com"""
        await ctx.send(
            f"Check out this actively maintained activity-based and auto-sorted "
            f"list of InfoSec streamers: https://infosecstreams.com"
        )

    @commands.command(aliases=["deaths", "death", "dead", "died", "ded", "dc"])
    async def death_counter(self, ctx: commands.Context):
        """type !death_counter appended with a plus (+) or minus (-) to increase/decrease the death counter"""
        if ctx.channel.name not in self.death_count:
            self.death_count[ctx.channel.name] = 0  # Add key if it doesn't exist
        if str(ctx.message.content).count("reset") >= 1:
            self.death_count[ctx.channel.name] = 0  # Reset key to 0
        else:
            try:
                param: str = str(ctx.message.content).split(maxsplit=1)[1]
                match = re.match(r"^([=+-])(\d+)$", param)
                if match:
                    sign = match.group(1)
                    num = int(match.group(2))
                    if sign == "=":
                        self.death_count[ctx.channel.name] = num
                    elif sign == "+":
                        self.death_count[ctx.channel.name] += num
                    elif sign == "-":
                        self.death_count[ctx.channel.name] -= num
                else:
                    plus_count = str(ctx.message.content).count("+")
                    minus_count = str(ctx.message.content).count("-")
                    self.death_count[ctx.channel.name] += (
                        plus_count - minus_count
                    )  # key equals the sum of +/- deaths
            except IndexError:
                pass
        await ctx.send(f"Deaths: {self.death_count[ctx.channel.name]}")

    @commands.command(aliases=["follow"])
    async def follow_channel(self, ctx: commands.Context):
        # TODO: use a headless browser to follow the channel
        """This endpoint is deprecated and will be shutdown on July 28, 2021. Applications that have not accessed
        this endpoint before 28 June 2021 can no longer call this endpoint. For more information, see
        https://discuss.dev.twitch.tv/t/deprecation-of-create-and-delete-follows-api-endpoints
        """
        # param: str = str(ctx.message.content).split(maxsplit=1)[1]
        # bot_user: list[twitchio.User] = await self.fetch_users(names=[settings.BOT_USER_ID])
        # bot_token_result_set = self.database.fetch_user_access_token(broadcaster_login=settings.BOT_USER_ID)
        # to_follow_user: list[twitchio.User] = await self.fetch_users(names=[param])
        # await to_follow_user[0].follow(userid=int(bot_user[0].id), token=dict(bot_token_result_set)['access_token'])
        pass

    # @commands.command(aliases=['mod'])
    # TODO: Update to dynamodb
    # async def mod_bot(self, ctx: commands.Context):
    #     from_broadcaster: PartialUser = list(filter(lambda x: x.name == ctx.channel.name, self.channel_broadcasters))[0]
    #     to_moderator_user = await self._http.get_users(ids=[], logins=[settings.BOT_USER_ID])
    #     await from_broadcaster.add_channel_moderator(token=self.user_token,
    #                                                  user_id=to_moderator_user[0]['id'])

    # @commands.command()
    # TODO: Update to dynamodb
    # async def add_channel_subs(self, ctx: commands.Context):
    #     subs = await self._http.get_channel_subscriptions(token=self.user_token,
    #                                                       broadcaster_id=user_result_set[0]['broadcaster_id'])
    #     self.database.update_all_subs_inactive()
    #     for sub in subs:
    #         try:
    #             self.database.insert_sub_data(broadcaster_id=sub['broadcaster_id'],
    #                                           broadcaster_login=sub['broadcaster_login'],
    #                                           broadcaster_name=sub['broadcaster_name'],
    #                                           gifter_id=sub['gifter_id'], gifter_login=sub['gifter_login'],
    #                                           gifter_name=sub['gifter_name'], is_gift=sub['is_gift'],
    #                                           plan_name=sub['plan_name'], tier=sub['tier'], user_id=sub['user_id'],
    #                                           user_name=sub['user_name'], user_login=sub['user_login'], is_active=True)
    #         except sqlite3.IntegrityError:
    #             print(f"Row already exists")

    @commands.command(aliases=["vt"])
    async def virustotal(self, ctx: commands.Context):
        """
        VirusTotal API Limits:
            Request rate	4 lookups / min
            Daily quota	    500 lookups / day
            Monthly quota	15.5 K lookups / month
        """
        param: str = str(ctx.message.content).split(" ")[1]
        vt = VirusTotalApiClient()
        if param == "-h" or param == "--h" or param == "-help" or param == "--help":
            await ctx.send(
                f"Usage: !virustotalsdf <hash>"
                f"This command checks a file hash against the VirusTotal "
                f"database to determine if it is a known malicious file."
                f"Arguments:"
                f"   <hash>  Required. The file hash to check against the VirusTotal database."
                f"Examples:"
                f"   virustotalsdf 83b79423cfea613fcb89c01f1717a852ea05e986aa3c3b1de17c314680b8d893"
                f"   virustotalsdf 6c0e6e35b9c9d1a25f1c92fb90f8fe03"
                f"Options:"
                f"   -h, --help    Show this help message and exit."
            )

        elif re.match(
            r"^(http(s)?(://)?)?(www\.)?(\w{0,253})(\.)(\w{2,})([/\w]*)$", param
        ):
            """type !virustotalsdf <domain> to lookup a domain on virustotalsdf"""
            try:
                domain_report = await vt.get_url_report(url=param)
                report_output: list[str] = ["VirusTotal -> "]
                (
                    report_output.append(f"url: {domain_report.url}, ")
                    if hasattr(domain_report, "url")
                    else None
                )
                (
                    report_output.append(
                        f"last_final_url: {domain_report.last_final_url}, "
                    )
                    if hasattr(domain_report, "last_final_url")
                    else None
                )
                (
                    report_output.append(f"title: {domain_report.title}, ")
                    if hasattr(domain_report, "title")
                    else None
                )
                (
                    report_output.append(
                        f"first_submission_date: {domain_report.first_submission_date}, "
                    )
                    if hasattr(domain_report, "first_submission_date")
                    else None
                )
                (
                    report_output.append(
                        f'last_analysis_stats["harmless"]: {domain_report.last_analysis_stats["harmless"]}, '
                    )
                    if hasattr(domain_report, "last_analysis_stats")
                    else None
                )
                (
                    report_output.append(
                        f'last_analysis_stats["malicious"]: {domain_report.last_analysis_stats["malicious"]}, '
                    )
                    if hasattr(domain_report, "last_analysis_stats")
                    else None
                )
                (
                    report_output.append(
                        f'total_votes["harmless"]: {domain_report.total_votes["harmless"]}, '
                    )
                    if hasattr(domain_report, "total_votes")
                    else None
                )
                (
                    report_output.append(
                        f'total_votes["malicious"]: {domain_report.total_votes["malicious"]}, '
                    )
                    if hasattr(domain_report, "total_votes")
                    else None
                )
                (
                    report_output.append(
                        f"times_submitted: {domain_report.times_submitted}!"
                    )
                    if hasattr(domain_report, "times_submitted")
                    else None
                )
                await ctx.send("".join(report_output))

                # if hasattr(domain_report, 'crowdsourced_ai_results'):
                # chatbot = Chatbot(settings.BARD_SECURE_1PSID)
                # response = chatbot.ask(f"Reduce this text to only 500 characters: "
                #                        f"```{domain_report.crowdsourced_ai_results[0]['analysis']}```.")
                # start = response['content'].find('\n\n') + 2
                # end = response['content'].find('\n\n', start)
                # await ctx.channel.send(f"{response['content'][start:end][:500]}")

            except Exception as error:
                await ctx.send(f"There's no VirusTotal report for this URL! {error}")

        else:
            """type !virustotalsdf <hash> to lookup a hash on virustotalsdf"""
            try:
                file_report = await vt.get_file_report(hash_id=param)
                report_output: list[str] = ["VirusTotal -> "]
                (
                    report_output.append(
                        f"meaningful_name: {file_report.meaningful_name}, "
                    )
                    if hasattr(file_report, "meaningful_name")
                    else None
                )
                (
                    report_output.append(f"magic: {file_report.magic}, ")
                    if hasattr(file_report, "magic")
                    else None
                )
                (
                    report_output.append(
                        f"popular_threat_classification: "
                        f'{file_report.popular_threat_classification["suggested_threat_label"]}, '
                    )
                    if hasattr(file_report, "popular_threat_classification")
                    else None
                )
                (
                    report_output.append(
                        f"first_seen_itw_date: {file_report.first_seen_itw_date}, "
                    )
                    if hasattr(file_report, "first_seen_itw_date")
                    else None
                )
                (
                    report_output.append(
                        f'last_analysis_stats["harmless"]: {file_report.last_analysis_stats["harmless"]}, '
                    )
                    if hasattr(file_report, "last_analysis_stats")
                    else None
                )
                (
                    report_output.append(
                        f'last_analysis_stats["malicious"]: {file_report.last_analysis_stats["malicious"]}, '
                    )
                    if hasattr(file_report, "last_analysis_stats")
                    else None
                )
                (
                    report_output.append(
                        f'total_votes["harmless"]: {file_report.total_votes["harmless"]}, '
                    )
                    if hasattr(file_report, "total_votes")
                    else None
                )
                (
                    report_output.append(
                        f'total_votes["malicious"]: {file_report.total_votes["malicious"]}, '
                    )
                    if hasattr(file_report, "total_votes")
                    else None
                )
                (
                    report_output.append(
                        f"times_submitted: {file_report.times_submitted}!"
                    )
                    if hasattr(file_report, "times_submitted")
                    else None
                )
                await ctx.send("".join(report_output))

                # if hasattr(file_report, 'crowdsourced_ai_results'):
                #     chatbot = Chatbot(settings.BARD_SECURE_1PSID)
                #     response = chatbot.ask(f"Reduce this text to only 500 characters: "
                #                            f"```{file_report.crowdsourced_ai_results[0]['analysis']}```.")
                #     start = response['content'].find('\n\n') + 2
                #     end = response['content'].find('\n\n', start)
                #     await ctx.channel.send(f"{response['content'][start:end][:500]}")

            except Exception as error:
                await ctx.send(f"There's no VirusTotal report for this hash! {error}")

    # TODO: add some discord commands https://discordpy.readthedocs.io/en/stable/
    @commands.command()
    async def discord(self, ctx: commands.Context):
        """type !discord to do something with discord"""
        await ctx.send(f"Hello {ctx.author.name}!")

    @commands.command()
    async def lurk(self, ctx: commands.Context):
        """type !lurk to let the streamer know you're lurking"""
        await ctx.send(
            f"{ctx.author.name} is watching the stream with the /silent flag!"
        )

    # @commands.command()
    # TODO: Update to dynamodb
    # async def raids(self, ctx: commands.Context):
    #     """ type !raids @username to print out how many raids you've received from the user """
    #     param_username = re.sub(r"^@", "", str(ctx.message.content).split(' ')[1])
    #     if len(param_username) >= 1:
    #         raider_login_result_set: sqlite3.Row = self.database.fetch_raids(raider_login=param_username.lower(),
    #                                                                          receiver_login=ctx.channel.name)
    #         await ctx.send(f"{param_username} has raided the channel {len(raider_login_result_set)} times!")

    # @commands.command()
    # TODO: Update to dynamodb
    # async def redemptions(self, ctx: commands.Context):
    #     """ type !redemptions to force the custom redemptions to load """
    #     broadcaster: PartialUser = list(filter(lambda x: x.name == ctx.channel.name, self.channel_broadcasters))[0]
    #     if int(ctx.author.id) == broadcaster.id or int(ctx.author.id) == 125444292:
    #         # Delete custom rewards before attempting to create new ones otherwise create_reward() will fail
    #         await self.delete_all_custom_rewards(broadcaster)
    #         # Add new custom rewards
    #         await self.add_kill_my_shell_redemption_reward(broadcaster)
    #         await self.add_vip_auto_redemption_reward(broadcaster)

    @commands.command(aliases=["so"])
    async def shoutout(self, ctx: commands.Context):
        """type !shoutout <@username> to shout out a viewers channel"""
        param_username = re.sub(r"^@", "", str(ctx.message.content).split(" ")[1])
        if len(param_username) >= 1:
            to_shoutout_user = await self._http.get_users(
                ids=[], logins=[param_username]
            )
            to_shoutout_channel = await self._http.get_channels(
                broadcaster_id=to_shoutout_user[0]["id"]
            )
            from_broadcaster: list[User] = await self.fetch_users(
                names=[ctx.channel.name]
            )
            await self.announce_shoutout(
                ctx=ctx,
                broadcaster=from_broadcaster[0],
                channel=to_shoutout_channel[0],
                color="blue",
            )
