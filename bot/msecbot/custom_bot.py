import json
import logging
import random
import re
from typing import List, Optional, Union

import boto3
import twitchio
from botocore.exceptions import ClientError
from colorama import Back, Fore, Style
from twitchio import (
    Channel,
    ChannelInfo,
    Clip,
    HTTPException,
    PartialUser,
    Unauthorized,
    User,
)
from twitchio.ext import commands, eventsub
from twitchio.ext.eventsub import (
    ChannelCharityDonationData,
    ChannelRaidData,
    ChannelSubscribeData,
    ChannelSubscriptionGiftData,
    StreamOfflineData,
    StreamOnlineData,
)

from bot.msecbot.api.virustotal.virus_total_api import VirusTotalApiClient
from bot.msecbot.config.bot_config import BotConfig
from bot.msecbot.esclient import CustomEventSubClient
from bot.msecbot.psclient import CustomPubSubClient
from bot.msecbot.utils.utils import Utils

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class CustomBot(commands.Bot):
    """
    ██████   ██████  ████████      ██████  ██████  ███    ███ ███    ███  █████  ███    ██ ██████  ███████
    ██   ██ ██    ██    ██        ██      ██    ██ ████  ████ ████  ████ ██   ██ ████   ██ ██   ██ ██
    ██████  ██    ██    ██        ██      ██    ██ ██ ████ ██ ██ ████ ██ ███████ ██ ██  ██ ██   ██ ███████
    ██   ██ ██    ██    ██        ██      ██    ██ ██  ██  ██ ██  ██  ██ ██   ██ ██  ██ ██ ██   ██      ██
    ██████   ██████     ██         ██████  ██████  ██      ██ ██      ██ ██   ██ ██   ████ ██████  ███████
    Start the eventsub client for the Twitch channel
    https://twitchio.dev/en/stable/exts/commands.html
    """

    config: BotConfig
    bot_user: PartialUser | User
    bot_oauth_token: str

    def __init__(self, config: BotConfig):
        self.config = config
        super().__init__(
            prefix="!",
            token=self.config.BOT_OAUTH_TOKEN,
            client_secret=self.config.CLIENT_SECRET,
            initial_channels=[self.config.BOT_INITIAL_CHANNELS[0].get("login")],
        )
        self.bot_oauth_token = self.config.BOT_OAUTH_TOKEN

        if self.config.get_bot_config().get("bot_features").get("enable_psclient"):
            for channel in self.config.BOT_INITIAL_CHANNELS:
                self.ps_client = CustomPubSubClient(
                    bot=self,
                    users_channel_id=int(channel.get("id")),
                    bot_oauth_token=self.bot_oauth_token,
                )

        if self.config.get_bot_config().get("bot_features").get("enable_esclient"):
            eventsub_public_url = None
            try:
                region_name = self.config.get_bot_config().get("aws").get("region_name")
                self.ec2 = boto3.client("ec2", region_name=region_name)
                # TODO: Don't hardcode InstanceIds
                response = self.ec2.describe_instances(
                    InstanceIds=["i-0100638f13e5451d8"]
                )
                if response.get("Reservations"):
                    public_dns_name = (
                        response.get("Reservations")[0]
                        .get("Instances")[0]
                        .get("PublicDnsName")
                    )
                    eventsub_public_url = f"https://{public_dns_name}"
                if eventsub_public_url:
                    self.es_client: CustomEventSubClient = CustomEventSubClient(
                        client=self,
                        webhook_secret="some_secret_string",
                        callback_route=f"{eventsub_public_url}",
                        bot_oauth_token=self.bot_oauth_token,
                    )
            except ClientError as client_error:
                logger.error(msg=client_error)

        # TODO: Make persistent
        self.death_count = {}

        """ load commands from cogs """
        if (
            self.config.get_bot_config()
            .get("bot_features")
            .get("cogs")
            .get("rce_cog")
            .get("enable_rce_cog")
        ):
            from bot.msecbot.cogs.rce import RCECog

            self.add_cog(RCECog(bot=self))

        if (
            self.config.get_bot_config()
            .get("bot_features")
            .get("cogs")
            .get("vip_cog")
            .get("enable_vip_cog")
        ):
            from bot.msecbot.cogs.vip import VIPCog

            self.add_cog(VIPCog(bot=self))

        @self.event()
        async def event_error(error: Exception, data: Optional[str] = None):
            logger.error(
                f"{Fore.RED}======================================================================== \n"
                f"Event Error: '{error}'! \n"
                f"Event Data: '{data}'! \n"
                f"======================================================================={Style.RESET_ALL}"
            )

        @self.event()
        async def event_channel_join_failure(_channel: str):
            logger.error(
                f"{Fore.RED}Bot failed to join {Fore.MAGENTA}{_channel}{Fore.RED} channel!{Style.RESET_ALL}"
            )
            # TODO: Auto refresh token and rejoin on failure
            await Utils().check_valid_token(user=self.bot_user)
            await self.join_channels(list(_channel))

        @self.event()
        async def event_channel_joined(_channel):
            logger.info(
                f"{Fore.LIGHTWHITE_EX}Bot successfully joined {Fore.LIGHTCYAN_EX}{_channel}"
                f"{Fore.LIGHTWHITE_EX}!{Style.RESET_ALL}"
            )
            logger.info(
                f"{Fore.LIGHTWHITE_EX}Connected_channels: {Fore.LIGHTCYAN_EX}{self.connected_channels}"
                f"{Fore.LIGHTWHITE_EX}!{Style.RESET_ALL}"
            )
            if self.config.get_bot_config().get("bot_features").get("announce_join"):
                await _channel.send(f"has joined chat! PowerUpL EntropyWins PowerUpR")
            if self.config.get_bot_config().get("bot_features").get("enable_esclient"):
                # Side effect of joining channel it should start listening to event subscriptions
                broadcasters: List[User] = await self.fetch_users(names=[_channel.name])
                await self.es_client.delete_event_subscriptions(broadcasters)
                await self.es_client.subscribe_channel_events(
                    broadcaster=broadcasters[0], moderator=broadcasters[0]
                )

        @self.event()
        async def event_join(_channel, user):
            logger.debug(
                f"{Fore.MAGENTA}JOIN{Fore.WHITE} is received from Twitch for user {Fore.CYAN}{user.name}{Fore.WHITE}"
                f" in channel {Fore.CYAN}{_channel.name}{Fore.WHITE}!{Style.RESET_ALL}"
            )
            pass

        @self.event()
        async def event_part(user):
            logger.debug(
                f"{Fore.MAGENTA}PART{Fore.WHITE} is received from Twitch for user {Fore.CYAN}"
                f"{user.name}{Style.RESET_ALL}"
            )
            pass

        @self.event()
        async def event_eventsub_notification_followV2(
            payload: eventsub.NotificationEvent,
        ) -> None:
            """event triggered when someone follows the channel"""
            logger.info(
                f"{Fore.LIGHTWHITE_EX}[{Fore.LIGHTRED_EX}{payload.data.broadcaster.name}{Fore.LIGHTWHITE_EX}]"
                f"{Fore.LIGHTBLUE_EX}[{Fore.LIGHTRED_EX}Follow{Fore.LIGHTWHITE_EX}]"
                f"{Fore.LIGHTBLUE_EX}[{Fore.YELLOW}EventSub{Fore.LIGHTWHITE_EX}]: "
                f"{Fore.LIGHTYELLOW_EX}{payload.data.user.name} {Fore.LIGHTWHITE_EX}"
                f"[{Fore.LIGHTYELLOW_EX}{payload.data.user.id}{Fore.LIGHTWHITE_EX}]{Style.RESET_ALL}"
            )
            await self.get_channel(payload.data.broadcaster.name).send(
                f"Thank you {payload.data.user.name} for following the channel!"
            )

        @self.event()
        async def event_eventsub_notification_cheer(
            payload: eventsub.NotificationEvent,
        ) -> None:
            """
            Event triggered when someone cheers in the channel.
            https://twitchio.dev/en/latest/exts/eventsub.html#twitchio.ext.eventsub.ChannelCheerData
            """
            cheer_data: eventsub.ChannelCheerData = payload.data

            # Get cheerer info
            channel_cheer_happened_in: Optional[Channel] = (
                cheer_data.broadcaster.channel
            )
            chatter_who_cheered = channel_cheer_happened_in.get_chatter(
                name=cheer_data.user.name
            )
            user_clips: List[Clip] = await cheer_data.user.fetch_clips(is_featured=True)

            if hasattr(cheer_data, "is_anonymous") and cheer_data.is_anonymous:
                event_string = (
                    f"Received cheer event from anonymous, "
                    f"cheered {cheer_data.bits} bits, "
                    f"message '{cheer_data.message}'."
                )
            else:
                event_string = (
                    f"Received cheer event from {cheer_data.user.name} [{cheer_data.user.id}], "
                    f"cheered {cheer_data.bits} bits, "
                    f"message '{cheer_data.message}'."
                )
            logger.info(
                f"{Fore.RED}[{cheer_data.broadcaster.name}]{Fore.BLUE}[Cheer]{Fore.RED}[EventSub]: "
                f"{event_string}{Style.RESET_ALL}"
            )

            # create stream marker (Stream markers cannot be created when the channel is offline)
            await self.set_stream_marker(payload=payload, event_string=event_string)

            # react to event
            if hasattr(cheer_data, "is_anonymous") and not cheer_data.is_anonymous:

                # Acknowledge raid and reply with a channel bio
                await channel_cheer_happened_in.send(
                    f"Thank you {chatter_who_cheered.mention} for cheering {cheer_data.bits} bits!"
                )
                # shoutout the subscriber
                if len(user_clips) >= 1:
                    """check if sub is a streamer with clips on their channel and shoutout with clip player"""
                    await channel_cheer_happened_in.send(
                        f"!so {chatter_who_cheered.mention}"
                    )
                    await self.announce_shoutout(
                        broadcaster=cheer_data.broadcaster,
                        user_to_shoutout=cheer_data.user,
                        color="green",
                    )
                else:
                    """shoutout without clip player"""
                    await self.announce_shoutout(
                        broadcaster=cheer_data.broadcaster,
                        user_to_shoutout=cheer_data.user,
                        color="green",
                    )

        @self.event()
        async def event_eventsub_notification_subscription(
            payload: eventsub.NotificationEvent,
        ) -> None:
            """
            Event triggered when someone subscribes in the channel.
            https://twitchio.dev/en/latest/exts/eventsub.html#twitchio.ext.eventsub.ChannelSubscribeData
            https://twitchio.dev/en/latest/exts/eventsub.html#twitchio.ext.eventsub.ChannelSubscriptionGiftData
            """
            channel_subscribe_data: (
                ChannelSubscribeData | ChannelSubscriptionGiftData
            ) = payload.data

            # Get subscriber info
            channel_subscription_happened_in: Optional[Channel] = (
                channel_subscribe_data.broadcaster.channel
            )
            chatter_who_subscribed = channel_subscription_happened_in.get_chatter(
                name=channel_subscribe_data.user.name
            )
            user_clips: List[Clip] = await channel_subscribe_data.user.fetch_clips(
                is_featured=True
            )

            # Check if sub is gifted
            if not channel_subscribe_data.is_gift:
                """event triggered when someone subscribes the channel"""
                if (
                    hasattr(channel_subscribe_data, "is_anonymous")
                    and channel_subscribe_data.is_anonymous
                ):
                    event_string = (
                        f"Received subscription event from anonymous, "
                        f"with tier {channel_subscribe_data.tier / 1000} sub."
                    )
                else:
                    event_string = (
                        f"Received subscription event from {channel_subscribe_data.user.name} [{channel_subscribe_data.user.id}], "
                        f"with tier {channel_subscribe_data.tier / 1000} sub."
                    )
                logger.info(
                    f"{Fore.RED}[{channel_subscribe_data.broadcaster.name}]{Fore.BLUE}[Sub]{Fore.RED}[EventSub]: "
                    f"{event_string}{Style.RESET_ALL}"
                )

                # create stream marker (Stream markers cannot be created when the channel is offline)
                await self.set_stream_marker(payload=payload, event_string=event_string)

                # Acknowledge raid and reply with a channel bio
                await channel_subscription_happened_in.send(
                    f"Thank you {chatter_who_subscribed.mention} for the tier {channel_subscribe_data.tier / 1000} "
                    f"subscription!"
                )

                # shoutout the subscriber
                if len(user_clips) >= 1:
                    # check if sub is a streamer with clips on their channel and shoutout with clip player
                    await channel_subscription_happened_in.send(
                        f"!so {chatter_who_subscribed.mention}"
                    )
                await self.announce_shoutout(
                    broadcaster=channel_subscribe_data.broadcaster,
                    user_to_shoutout=channel_subscribe_data.user,
                    color="green",
                )

            else:
                """event triggered when someone gifts a sub to someone in the channel"""
                if (
                    hasattr(channel_subscribe_data, "is_anonymous")
                    and channel_subscribe_data.is_anonymous
                ):
                    event_string = (
                        f"Received gift subscription event from anonymous, "
                        f"with tier {int(channel_subscribe_data.tier / 1000)} sub. [GIFTED]"
                    )
                else:
                    event_string = (
                        f"Received gift subscription event from {channel_subscribe_data.user.name} "
                        f"[{channel_subscribe_data.user.id}], with tier {int(channel_subscribe_data.tier / 1000)} sub. [GIFTED]"
                    )
                logger.info(
                    f"{Fore.RED}[{channel_subscribe_data.broadcaster.name}]{Fore.BLUE}[GiftSub]{Fore.RED}[EventSub]: "
                    f"{event_string}{Style.RESET_ALL}"
                )

                # create stream marker (Stream markers cannot be created when the channel is offline)
                await self.set_stream_marker(payload=payload, event_string=event_string)

                # Get subscriber info and acknowledge raid with reply containing channel bio
                await channel_subscription_happened_in.send(
                    f"Congratulations {chatter_who_subscribed.mention} on receiving a "
                    f"gifted tier {int(channel_subscribe_data.tier / 1000)} subscription!"
                )

        @self.event()
        async def event_eventsub_notification_raid(
            payload: eventsub.NotificationEvent,
        ) -> None:
            """event triggered when someone raids the channel"""
            channel_raid_data: ChannelRaidData = payload.data

            # Get raid info
            channel_raid_happened_in: Optional[Channel] = (
                channel_raid_data.reciever.channel
            )
            chatter_who_raided = channel_raid_happened_in.get_chatter(
                name=channel_raid_data.raider.name
            )
            user_clips: List[Clip] = await channel_raid_data.raider.fetch_clips(
                is_featured=True
            )

            event_string = (
                f"Received raid event from {chatter_who_raided.mention} [{channel_raid_data.raider.id}], "
                f"with {channel_raid_data.viewer_count} viewers"
            )
            logger.info(
                f"{Fore.RED}[{channel_raid_data.reciever.name}]{Fore.BLUE}[Raid]{Fore.RED}[EventSub]: "
                f"{event_string}{Style.RESET_ALL}"
            )

            # TODO: Persist the raid occurrence in dynamodb
            # db.insert_raid_data(raider_id=data.raider.id, raider_login=data.raider.name,
            #                     receiver_id=data.reciever.id, receiver_login=data.reciever.name,
            #                     viewer_count=data.viewer_count)

            # create stream marker (Stream markers cannot be created when the channel is offline)
            await self.set_stream_marker(payload=payload, event_string=event_string)

            # Acknowledge raid and reply with a channel bio
            await channel_raid_happened_in.send(
                f"TombRaid TombRaid TombRaid WELCOME RAIDERS!!! "
                f"Thank you {chatter_who_raided.mention} for trusting me with your community!"
            )

            # shoutout the raider
            if len(user_clips) >= 1:
                # check if raider is a streamer with clips on their channel and shoutout with clip player
                await channel_raid_happened_in.send(f"!so {chatter_who_raided.mention}")
            await self.announce_shoutout(
                broadcaster=channel_raid_data.reciever,
                user_to_shoutout=channel_raid_data.raider,
                color="orange",
            )

        @self.event()
        async def event_eventsub_notification_stream_start(
            payload: eventsub.NotificationEvent,
        ) -> None:
            """event triggered when stream goes live"""
            data: StreamOnlineData = payload.data

            logger.info(
                f"{Fore.RED}[{data.broadcaster.name}]{Fore.BLUE}[StreamOnline]{Fore.RED}[EventSub]: "
                f"type={data.type}, started_at={data.started_at}.{Style.RESET_ALL}"
            )

            # Delete custom rewards before attempting to create new ones otherwise create_reward() will fail
            await self.delete_all_custom_rewards(data.broadcaster)

            # Add new custom rewards
            await self.add_kill_my_shell_redemption_reward(data.broadcaster)
            await self.add_vip_auto_redemption_reward(data.broadcaster)

            # Announce event in chat
            await data.broadcaster.channel.send(f"This stream is now online!")

        @self.event()
        async def event_eventsub_notification_stream_end(
            payload: eventsub.NotificationEvent,
        ) -> None:
            """event triggered when stream goes offline"""
            data: StreamOfflineData = payload.data

            logger.info(
                f"{Fore.RED}[{payload.data.broadcaster.name}]{Fore.BLUE}[StreamOffline]{Fore.RED}"
                f"[EventSub]: {Style.RESET_ALL}"
            )

            # Delete custom rewards before attempting to create new ones otherwise create_reward() will fail
            await self.delete_all_custom_rewards(payload.data.broadcaster)

            # Announce event in chat
            await data.broadcaster.channel.send(f"This stream is now offline!")

        @self.event()
        async def event_eventsub_notification_channel_charity_donate(
            payload: eventsub.NotificationEvent,
        ) -> None:
            """event triggered when user donates to an active charity campaign"""
            data: ChannelCharityDonationData = payload.data

            logger.info(
                f"{Fore.RED}[{data.broadcaster.name}]{Fore.BLUE}[ChannelCharityDonation]{Fore.RED}"
                f"[EventSub]: {Style.RESET_ALL}"
            )

            currency_symbols = Utils.get_currency_symbols()
            donation_value = data.donation_value / (10**data.donation_decimal_places)
            await self._http.post_chat_announcement(
                f"{data.user.name} has donated {currency_symbols.get(data.donation_currency)}{donation_value} "
                f"towards the charity fundraiser for {data.charity_name}! Thank you! You "
                f"can learn more about the charity here: {data.charity_website}"
            )

    async def __ainit__(self):
        self.bot_user: User = (
            await self.fetch_users(ids=[int(self.config.BOT_USER_ID)])
        )[0]

    async def __validate__(self):
        validate_result = await self._http.validate(token=self.config.BOT_OAUTH_TOKEN)
        logger.info(
            f"{Fore.LIGHTGREEN_EX}Validation complete: {validate_result}{Style.RESET_ALL}"
        )

    async def __psclient_init__(self) -> None:
        if self.config.get_bot_config().get("bot_features").get("enable_psclient"):
            await self.ps_client.start_pubsub()

    async def __esclient_init__(self) -> None:
        if self.config.get_bot_config().get("bot_features").get("enable_esclient"):
            await self.es_client.delete_all_event_subscriptions()
            await self.es_client.subscribe_channel_events(
                broadcaster=None, moderator=None
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
                    token=self.config.BOT_OAUTH_TOKEN, description=event_string
                )
            else:
                await payload.data.broadcaster.create_marker(
                    token=self.config.BOT_OAUTH_TOKEN, description=event_string
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
            logger.info("Bot detected")
            return True
        return False

    async def event_ready(self):
        if len(self.connected_channels) == 0:
            """Bot failed to join channel."""
            await self.join_channels(
                channels=[
                    self.config.get_bot_config()
                    .get("twitch")
                    .get("channel")
                    .get("bot_join_channel")
                ]
            )

        if len(self.connected_channels) >= 1:
            """Bot is logged into IRC and ready to do its thing."""
            # logins = [channel.name for channel in self.connected_channels]
            # user_data = await self._http.get_users(token=self._http.app_token, ids=[], logins=logins)
            for channel in self.connected_channels:
                logger.info(
                    f"{Fore.LIGHTWHITE_EX}[{Fore.LIGHTBLUE_EX}BOT READY{Fore.LIGHTWHITE_EX}] Logged into channel(s): "
                    f"{Fore.LIGHTBLUE_EX}{channel.name}{Fore.LIGHTWHITE_EX}, "
                    f"as bot user: {Fore.LIGHTBLUE_EX}{self.nick}{Fore.LIGHTWHITE_EX} "
                    f"({Fore.LIGHTBLUE_EX}ID: {self.user_id}{Fore.LIGHTWHITE_EX})!{Style.RESET_ALL}"
                )

            if (
                self.config.get_bot_config()
                .get("bot_features")
                .get("cogs")
                .get("ascii_cog")
                .get("enable_ascii_cog")
            ):
                from bot.msecbot.cogs.ascii_cog import AsciiCog

                self.add_cog(AsciiCog(self))

    async def event_message(self, message: twitchio.Message):
        """Messages with echo set to True are messages sent by the bot. ignore them."""
        if message.echo:
            return
        # Print the contents of our message to console...
        include_channel = (
            f"{Fore.LIGHTWHITE_EX}[{Back.BLACK}{Style.BRIGHT}📽{Fore.LIGHTWHITE_EX}: "
            f"{Fore.LIGHTWHITE_EX}{str.upper(message.channel.name)}{Back.RESET}{Style.RESET_ALL}{Fore.LIGHTWHITE_EX}]"
        )
        include_author = (
            f"{Fore.LIGHTWHITE_EX}[{Back.BLACK}{Style.BRIGHT}‍🧏🏼‍️️{Fore.LIGHTWHITE_EX}: "
            f"{Fore.LIGHTWHITE_EX}{str.upper(message.author.name)}{Back.RESET}{Style.RESET_ALL}{Fore.LIGHTWHITE_EX}]"
        )
        include_is_broadcaster = (
            (
                f"{Fore.LIGHTWHITE_EX}[{Back.RESET}{Style.BRIGHT}{Fore.RED}"
                f" 📽 BROADCASTER "
                f"{Back.RESET}{Style.RESET_ALL}{Fore.LIGHTWHITE_EX}]"
            )
            if message.author.is_broadcaster
            else ""
        )
        include_is_moderator = (
            (
                f"{Fore.LIGHTWHITE_EX}[{Back.RESET}{Style.BRIGHT}{Fore.GREEN}"
                f" ⚒ MOD "
                f"{Back.RESET}{Style.RESET_ALL}{Fore.LIGHTWHITE_EX}️]"
            )
            if message.author.is_mod
            else ""
        )
        include_is_subscriber = (
            (
                f"{Fore.LIGHTWHITE_EX}[{Back.GREEN}{Style.BRIGHT}{Fore.LIGHTWHITE_EX}"
                f" 💲 SUB "
                f"{Back.RESET}{Style.RESET_ALL}{Fore.LIGHTWHITE_EX}]"
            )
            if message.author.is_subscriber
            else ""
        )
        include_is_turbo = (
            (
                f"{Fore.LIGHTWHITE_EX}[{Back.YELLOW}{Style.BRIGHT}{Fore.LIGHTWHITE_EX}"
                f" ⚡ TURBO "
                f"{Back.RESET}{Style.RESET_ALL}{Fore.LIGHTWHITE_EX}]"
            )
            if bool(int(message.author.is_turbo))
            else ""
        )
        include_is_vip = (
            (
                f"{Fore.LIGHTWHITE_EX}[{Back.LIGHTMAGENTA_EX}{Style.BRIGHT}{Fore.LIGHTWHITE_EX}"
                f" ❤ VIP︎ "
                f"{Back.RESET}{Style.RESET_ALL}{Fore.LIGHTWHITE_EX}]"
            )
            if message.author.is_vip
            else ""
        )
        include_message = (
            f"{Fore.LIGHTWHITE_EX}: {Fore.WHITE}{message.content}{Style.RESET_ALL}"
        )
        logger.info(
            f"{include_channel}{include_author}"
            f"{include_is_broadcaster}"
            f"{include_is_moderator}"
            f"{include_is_subscriber}"
            f"{include_is_turbo}"
            f"{include_is_vip}"
            f"{include_message}"
        )

        """ Messages that include common bot spammer phrases auto-ban. """
        is_bot = await self.detect_bot_spam(message=message)
        if is_bot:
            user: PartialUser = await message.channel.user()
            # oauth user access token with the ``moderator:manage:banned_users`` scope
            await user.ban_user(
                token=self.config.BOT_OAUTH_TOKEN,
                moderator_id=user.id,
                user_id=int(message.author.id),
                reason="Banned for posting known bot spam/scam messages (eg: buy follows at dogehype)",
            )
        else:
            """Handle commands overriding the default `event_message`."""
            await self.handle_commands(message)

    async def add_kill_my_shell_redemption_reward(
        self, broadcaster: User | PartialUser
    ):
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
                token=self.config.BOT_OAUTH_TOKEN,
            )
            logger.info(
                f"{Fore.RED}Added {Fore.MAGENTA}'Kill My Shell'{Fore.RED} channel point redemption.{Style.RESET_ALL}"
            )

    async def add_vip_auto_redemption_reward(self, broadcaster: User | PartialUser):
        """Adds channel point redemption that adds the user to the VIP list automatically"""
        vips = await self._http.get_channel_vips(
            token=self.config.BOT_OAUTH_TOKEN, broadcaster_id=broadcaster.id, first=100
        )
        if len(vips) < int(
            self.config.get_bot_config()
            .get("twitch")
            .get("channel")
            .get("max_vip_slots")
        ):
            await self._http.create_reward(
                broadcaster_id=broadcaster.id,
                title="VIP",
                cost=80085,
                prompt="VIPs have the ability to equip a special chat badge and bypass the chat limit in slow mode!",
                max_per_user=1,
                global_cooldown=5 * 60,
                token=self.config.BOT_OAUTH_TOKEN,
            )
            logger.info(
                f"{Fore.RED}Added {Fore.MAGENTA}'VIP'{Fore.RED} channel point redemption.{Style.RESET_ALL}"
            )

    async def delete_all_custom_rewards(self, broadcaster: User | PartialUser):
        """deletes all custom rewards (API limits deletes to those created by the bot)
        Requires a user access token that includes the channel:manage:redemptions scope.
        """
        rewards = await self._http.get_rewards(
            broadcaster_id=broadcaster.id,
            only_manageable=True,
            token=self.config.BOT_OAUTH_TOKEN,
        )
        logger.info(
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
                    token=self.config.BOT_OAUTH_TOKEN,
                )
                logger.info(
                    f"{Fore.RED}Deleted reward: [{Fore.MAGENTA}id={reward['id']}{Fore.RED}]"
                    f"[{Fore.MAGENTA}title={reward['title']}{Fore.RED}]{Style.RESET_ALL}"
                )

    async def update_reward_redemption_status(
        self,
        broadcaster: User | PartialUser,
        reward_id: str,
        custom_reward_id: str,
        status: bool,
    ) -> None:
        self._http.update_reward_redemption_status(
            token=self.bot_oauth_token,
            broadcaster_id=broadcaster.id,
            reward_id=reward_id,
            custom_reward_id=custom_reward_id,
            status=status,
        )

    async def announce_shoutout(
        self,
        broadcaster: User | PartialUser,
        user_to_shoutout: User | PartialUser,
        color: str,
    ):
        message_builder: list[str] = [f"Please check out "]
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
        message_builder.append(random.choice(flattering_strings))
        channel_info: ChannelInfo = await self.fetch_channel(
            broadcaster=user_to_shoutout.id
        )
        message_builder.append(
            f" {user_to_shoutout.name}'s channel over at "
            f"(https://www.twitch.tv/{channel_info.user.name})!"
        )
        if not channel_info.game_name == "":
            message_builder.append(
                f" They were last playing '{channel_info.game_name}', title: '{channel_info.title}'."
            )

        error_count = 0
        try:
            await self.post_chat_announcement(
                broadcaster=broadcaster,
                message="".join(message_builder),
                moderator=self.bot_user,
                color=color,
            )

        except Exception as error:
            logger.error(
                f"{Fore.RED}Could not send shoutout announcement to {Fore.MAGENTA}{user_to_shoutout.name}"
                f"{Fore.RED} from channel {Fore.MAGENTA}{broadcaster.name}{Fore.RED}: {error}{Style.RESET_ALL}"
            )
            error_count += 1
            raise

        try:
            """Perform a Twitch Shoutout command (https://help.twitch.tv/s/article/shoutouts?language=en_US).
            The channel giving a Shoutout must be live AND you cannot shoutout the current streamer.
            """
            if user_to_shoutout.id != str(broadcaster.id):
                streams = await self._http.get_streams(user_ids=[broadcaster.id])
                if len(streams) >= 1 and streams[0]["type"] == "live":
                    # Moderator ID must match the user ID in the user access token.
                    await self.send_shoutout(
                        broadcaster=broadcaster,
                        to_broadcaster_id=user_to_shoutout.id,
                    )

        except Exception as error:
            """Eg: shoutout global cooldown "You have to wait 1m 30s before giving another Shoutout."""
            logger.error(
                f"{Fore.RED}Could not perform a Twitch Shoutout command to {Fore.MAGENTA}{user_to_shoutout.name}"
                f"{Fore.RED} from channel {Fore.MAGENTA}{broadcaster.name}{Fore.RED}: {error}{Style.RESET_ALL}"
            )
            raise

        if error_count >= 1:
            if broadcaster is not None and hasattr(broadcaster.channel, "send"):
                await broadcaster.channel.send("".join(message_builder))

    async def post_chat_announcement(
        self,
        broadcaster: User | PartialUser,
        moderator: User | PartialUser,
        message: str,
        color: str,
    ):
        """Post a shoutout announcement to chat; color = blue, green, orange, purple, or primary"""
        logger.info(
            f"{Fore.LIGHTWHITE_EX}Trying to send chat announcement as "
            f"Broadcaster ID: [{Fore.LIGHTRED_EX}{broadcaster.id}{Fore.LIGHTWHITE_EX}], "
            f"Moderator ID: [{Fore.LIGHTGREEN_EX}{moderator.id}{Fore.LIGHTWHITE_EX}], "
            f"and using token: [{Fore.LIGHTMAGENTA_EX}OAuth {Utils().redact_secret_string(self.bot_oauth_token)}"
            f"{Fore.LIGHTWHITE_EX}].{Style.RESET_ALL}"
        )
        try:
            await self._http.post_chat_announcement(
                token=self.bot_oauth_token,
                broadcaster_id=broadcaster.id,
                moderator_id=moderator.id,
                message=message,
                color=color,
            )
        except Unauthorized as error:
            # 401: You're not authorized to use this route.: incorrect user authorization
            logger.error(f"Error sending post_chat_announcement: {error}.")

    async def send_shoutout(
        self, broadcaster: PartialUser | User, to_broadcaster_id: int
    ):
        # TODO: Move to twitch commands util class
        await broadcaster.shoutout(
            token=self.bot_oauth_token,
            to_broadcaster_id=to_broadcaster_id,
            moderator_id=self.bot_user.id,
        )

    """
    COG COMMANDS BELOW ↓ ↓ ↓ ↓ ↓
    """

    @commands.command(aliases=["enablesounds"])
    async def sounds_on(self, ctx: commands.Context):
        from bot.msecbot.cogs.sounds_cog import SoundsCog

        self.add_cog(SoundsCog(self))
        await ctx.send(f"Sound Commands Enabled!")

    @commands.command(aliases=["disablesounds"])
    async def sounds_off(self, ctx: commands.Context):
        from bot.msecbot.cogs.sounds_cog import SoundsCog

        self.remove_cog(SoundsCog(self).name)
        await ctx.send(f"Sound Commands Disabled!")

    @commands.command()
    async def user_commands_on(self, ctx: commands.Context):
        from bot.msecbot.cogs.user_cog import UserCog

        self.add_cog(UserCog(self))
        await ctx.send(f"User Commands Enabled!")

    @commands.command()
    async def user_commands_off(self, ctx: commands.Context):
        from bot.msecbot.cogs.user_cog import UserCog

        self.remove_cog(UserCog(self).name)
        await ctx.send(f"User Commands Disabled!")

    """
    BOT COMMANDS BELOW ↓ ↓ ↓ ↓ ↓
    """

    @commands.command(aliases=["hi"])
    async def hello(self, ctx: commands.Context):
        """type !hello to say hello to author"""
        await ctx.send(f"Hello {ctx.author.name}!")

    @commands.command(aliases=["cls", "clr"])
    async def clear(self, ctx: commands.Context):
        """type !clear to clear chat messages"""
        broadcaster: User = (await self.fetch_users(ids=[], names=[ctx.channel.name]))[
            0
        ]
        bot_oauth = self.config.get_bot_config().get("twitch").get("bot_auth")
        await broadcaster.delete_chat_messages(
            token=bot_oauth.get("bot_oauth_token"),
            moderator_id=bot_oauth.get("bot_user_id"),
        )

    @commands.command()
    async def join(self, ctx: commands.Context):
        """type !join <channel> to join the channel"""
        try:
            param_username = re.sub(
                r"^@", "", str(ctx.message.content).split(maxsplit=1)[1]
            )
            # Limit to broadcaster
            if ctx.author.is_broadcaster or int(ctx.author.id) == 125444292:
                await self.join_channels([param_username])
        except IndexError:
            logger.error("!join command failed. Regex pattern did not match.")

    @commands.command(aliases=["fuckoffmsecbot"])
    async def leave(self, ctx: commands.Context):
        """type !leave <channel> to join the channel"""
        param_username = None
        try:
            param_username = re.sub(
                r"^@", "", str(ctx.message.content).split(maxsplit=1)[1]
            ).lower()
        except IndexError:
            logger.error(
                f"{Fore.LIGHTWHITE_EX}!leave command failed. Regex pattern did not match!{Style.RESET_ALL}"
            )

        initial_channels_set = {
            user["login"].lower()
            for user in self.config.get_bot_config()
            .get("twitch")
            .get("bot_initial_channels")
        }

        # AUTHORIZATION: Check that author is either the broadcaster, or msec;
        # and that the channel is not in the list of initial channels so the bot remains connected to a channel(s).
        if (
            ctx.author.is_broadcaster
            or int(ctx.author.id) == 125444292  # msec author id
        ) and param_username not in initial_channels_set:
            await self.part_channels([param_username])
            logger.info(
                f"{Fore.LIGHTWHITE_EX}Bot successfully parted channel {Fore.LIGHTCYAN_EX}{param_username}"
                f"{Fore.LIGHTWHITE_EX}!{Style.RESET_ALL}"
            )
            logger.info(
                f"{Fore.LIGHTWHITE_EX}Connected_channels: {Fore.LIGHTCYAN_EX}{self.connected_channels}"
                f"{Fore.LIGHTWHITE_EX}!{Style.RESET_ALL}"
            )

            # also remove event subscriptions for the channel
            if self.config.get_bot_config().get("bot_features").get("enable_esclient"):
                broadcasters: List[User] = await self.fetch_users(
                    names=[param_username]
                )
                await self.es_client.delete_event_subscriptions(
                    broadcasters=broadcasters
                )

    @commands.command(aliases=["stop", "close", "killyourselfmsecbot"])
    async def exit(self, ctx: commands.Context):
        """type !exit <channel> to stop the bot"""
        await super().close()
        exit()

    @commands.command()
    async def song(self, ctx: commands.Context):
        # TODO: Get currently playing song from rainwave
        # https://rainwave.cc/api4/help/api4/info
        pass

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
    #     from_broadcaster: PartialUser = list(filter(aws x: x.name == ctx.channel.name, self.channel_broadcasters))[0]
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
    #                                           user_name=sub['user_name'], user_login=sub['user_login'],
    #                                           is_active=True)
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

        if (
            self.config.get_bot_config()
            .get("bot_features")
            .get("virus_total")
            .get("enable_virus_total")
        ):
            vt = VirusTotalApiClient()
            param: str = str(ctx.message.content).split(" ")[1]
            if param == "-h" or param == "--h" or param == "-help" or param == "--help":
                await ctx.send(
                    f"Usage: !virustotal <hash>"
                    f"This command checks a file hash against the VirusTotal "
                    f"database to determine if it is a known malicious file."
                    f"Arguments:"
                    f"<hash> Required. The file hash to check against the VirusTotal database."
                    f"Examples:"
                    f"   virustotal 83b79423cfea613fcb89c01f1717a852ea05e986aa3c3b1de17c314680b8d893"
                    f"   virustotal 6c0e6e35b9c9d1a25f1c92fb90f8fe03"
                    f"Options:"
                    f"-h, --help    Show this help message and exit."
                )

            elif re.match(
                r"^(http(s)?(://)?)?(www\.)?(\w{0,253})(\.)(\w{2,})([/\w]*)$", param
            ):
                """type !virustotal <domain> to lookup a domain on VirusTotal"""
                try:
                    domain_report = await vt.get_url_report(url=param)
                    await self.send_domain_report(ctx=ctx, domain_report=domain_report)

                except Exception as error:
                    await ctx.send(
                        f"There's no VirusTotal report for this URL! {error}"
                    )
                    logger.error(
                        f"{Fore.LIGHTWHITE_EX}There's no VirusTotal report for this URL! "
                        f"{Fore.LIGHTRED_EX}{error}{Fore.LIGHTWHITE_EX}.{Style.RESET_ALL}"
                    )

            else:
                """type !virustotal <hash> to lookup a hash on VirusTotal"""
                try:
                    file_report = await vt.get_file_report(hash_id=param)
                    await self.send_file_report(ctx=ctx, file_report=file_report)

                except Exception as error:
                    await ctx.send(
                        f"There's no VirusTotal report for this hash! {error}"
                    )
                    logger.error(
                        f"{Fore.LIGHTWHITE_EX}There's no VirusTotal report for this hash! "
                        f"{Fore.LIGHTRED_EX}{error}{Fore.LIGHTWHITE_EX}.{Style.RESET_ALL}"
                    )
        else:
            # Delete the chat message
            try:
                broadcaster_id: int = (
                    await self.fetch_users(names=[ctx.channel.name])
                )[0].id
                logger.debug(
                    f"{Fore.LIGHTWHITE_EX}Deleting chat message. "
                    f"{Fore.LIGHTRED_EX}token{Fore.LIGHTWHITE_EX}: "
                    f"[{Fore.MAGENTA}OAuth {Utils.redact_secret_string(self.bot_oauth_token)}{Fore.LIGHTWHITE_EX}], "
                    f"{Fore.LIGHTRED_EX}broadcaster_id{Fore.LIGHTWHITE_EX}: "
                    f"{Fore.LIGHTYELLOW_EX}{broadcaster_id}{Fore.LIGHTWHITE_EX}, "
                    f"{Fore.LIGHTRED_EX}moderator_id{Fore.LIGHTWHITE_EX}: "
                    f"{Fore.LIGHTYELLOW_EX}{self.bot_user.id}{Fore.LIGHTWHITE_EX}, "
                    f"{Fore.LIGHTRED_EX}message_id{Fore.LIGHTWHITE_EX}: "
                    f"{Fore.LIGHTYELLOW_EX}{ctx.message.id}{Fore.LIGHTWHITE_EX}"
                    f"{Fore.LIGHTWHITE_EX}.{Style.RESET_ALL}"
                )
                await self._http.delete_chat_messages(
                    token=self.bot_oauth_token,
                    broadcaster_id=broadcaster_id,
                    moderator_id=self.bot_user.id,
                    message_id=ctx.message.id,
                )
            except HTTPException as error:
                logger.error(
                    f"{Fore.LIGHTWHITE_EX}Failed to delete chat message. "
                    f"{Fore.LIGHTRED_EX}{error}{Fore.LIGHTRED_EX}.{Style.RESET_ALL}"
                )
            # Send whisper
            try:
                await self.bot_user.send_whisper(
                    token=self.bot_oauth_token,
                    user_id=int(ctx.author.id),
                    message=f"Hey {ctx.author.name}, unfortunately the Virus Total feature has been disabled so that "
                    f"command won't work at this time.",
                )
                logger.info(
                    f"{Fore.LIGHTWHITE_EX}Whisper sent to user: {Fore.LIGHTCYAN_EX}{ctx.author.name}"
                    f"{Fore.LIGHTWHITE_EX}, explaining that the Virus Total feature is disabled.{Style.RESET_ALL}"
                )
            except HTTPException as error:
                logger.error(
                    f"{Fore.LIGHTWHITE_EX}Failed to send whisper to {ctx.author.name}, likely blocking from strangers. "
                    f"{Fore.LIGHTRED_EX}{error}{Fore.LIGHTWHITE_EX}.{Style.RESET_ALL}"
                )

    @staticmethod
    def append_if_exists(
        report_output: list[str],
        obj: Union[dict, object],
        attribute_path: str,
        label: str,
    ):
        # Traverse nested attributes if needed
        attrs = attribute_path.split(".")
        value = obj
        try:
            for attr in attrs:
                if isinstance(value, dict):
                    value = value[attr]
                else:
                    value = getattr(value, attr)
            report_output.append(f"{label}: {value}, ")
        except (AttributeError, KeyError):
            pass

    async def send_domain_report(self, ctx, domain_report):
        report_output = ["VirusTotal -> "]

        # Domain report attributes
        attributes = [
            ("url", "url"),
            ("last_final_url", "last_final_url"),
            ("title", "title"),
            ("first_submission_date", "first_submission_date"),
            ("last_analysis_stats.harmless", 'last_analysis_stats["harmless"]'),
            ("last_analysis_stats.malicious", 'last_analysis_stats["malicious"]'),
            ("total_votes.harmless", 'total_votes["harmless"]'),
            ("total_votes.malicious", 'total_votes["malicious"]'),
            ("times_submitted", "times_submitted"),
        ]

        # Append domain report details
        for attr_path, label in attributes:
            self.append_if_exists(report_output, domain_report, attr_path, label)

        report_output.append("!")
        await ctx.send("".join(report_output))

    async def send_file_report(self, ctx, file_report):
        report_output = ["VirusTotal -> "]

        # File report attributes
        attributes = [
            ("meaningful_name", "meaningful_name"),
            ("magic", "magic"),
            (
                "popular_threat_classification.suggested_threat_label",
                "popular_threat_classification",
            ),
            ("first_seen_itw_date", "first_seen_itw_date"),
            ("last_analysis_stats.harmless", 'last_analysis_stats["harmless"]'),
            ("last_analysis_stats.malicious", 'last_analysis_stats["malicious"]'),
            ("total_votes.harmless", 'total_votes["harmless"]'),
            ("total_votes.malicious", 'total_votes["malicious"]'),
            ("times_submitted", "times_submitted"),
        ]

        # Append file report details
        for attr_path, label in attributes:
            self.append_if_exists(report_output, file_report, attr_path, label)

        report_output.append("!")
        await ctx.send("".join(report_output))

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
    #     broadcaster: PartialUser = list(filter(aws x: x.name == ctx.channel.name, self.channel_broadcasters))[0]
    #     if int(ctx.author.id) == broadcaster.id or int(ctx.author.id) == 125444292:
    #         # Delete custom rewards before attempting to create new ones otherwise create_reward() will fail
    #         await self.delete_all_custom_rewards(broadcaster)
    #         # Add new custom rewards
    #         await self.add_kill_my_shell_redemption_reward(broadcaster)
    #         await self.add_vip_auto_redemption_reward(broadcaster)

    @commands.command(aliases=["so"])
    async def shoutout(self, ctx: commands.Context):
        """type !shoutout <@username> to shout out a viewers channel"""
        try:
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
        except IndexError:
            logger.error("!shoutout failed. No username supplied.")
        except Unauthorized as error:
            logger.error(f"!shoutout failed. {error}")
