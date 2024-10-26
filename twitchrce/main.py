import asyncio
import secrets
from typing import List, Optional

import boto3
import nest_asyncio
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from colorama import Fore, Style
from twitchio import User
from twitchio.ext import eventsub, pubsub

from twitchrce.api.twitch.twitch_api_auth import TwitchApiAuth
from twitchrce.cogs.rce import RCECog
from twitchrce.cogs.vip import VIPCog
from twitchrce.config import bot_config
from twitchrce.custom_bot import CustomBot

nest_asyncio.apply()


async def get_app_token() -> str:
    """Uses the bots' client id and secret to generate a new application token via client credentials grant flow"""
    client_creds_grant_flow = await TwitchApiAuth().client_credentials_grant_flow()
    print(
        f"{Fore.RED}Updated {Fore.MAGENTA}app access token{Fore.RED}!{Style.RESET_ALL}"
    )
    return client_creds_grant_flow["access_token"]


# TODO: Replace with lambda calls
async def check_valid_token(user: any) -> bool:
    """
    Asynchronously checks if a user's access token is valid. If the token is invalid,
    attempts to refresh the token and validates it again.

    Args:
        user (any): A user object or dictionary containing the user's access token
            under the key "access_token".

    Returns:
        bool: True if the user's access token is valid after validation or refresh;
              False if it remains invalid.
    """
    is_valid_token = await TwitchApiAuth().validate_token(
        access_token=user.get("access_token")
    )
    if not is_valid_token:
        access_token = await refresh_user_token(user=user)
        is_valid_token = await TwitchApiAuth().validate_token(access_token=access_token)
    return is_valid_token


# TODO: Replace with lambda calls
async def refresh_user_token(user: any) -> str:
    auth_result = await TwitchApiAuth().refresh_access_token(
        refresh_token=user.get("refresh_token")
    )
    try:
        # Insert the item
        user_table.update_item(
            Key={"id": user.get("id")},
            UpdateExpression="set access_token=:a, refresh_token=:r, expires_in=:e",
            ExpressionAttributeValues={
                ":a": auth_result.get("access_token"),
                ":r": auth_result.get("refresh_token"),
                ":e": auth_result.get("expires_in"),
            },
            ReturnValues="UPDATED_NEW",
        )
        print(
            f"{Fore.RED}Updated access and refresh token for {Fore.MAGENTA}{user['login']}{Fore.RED}!"
            f"{Style.RESET_ALL}"
        )
    except (NoCredentialsError, PartialCredentialsError) as error:
        print("Credentials not available")
        raise error
    return auth_result.get("access_token")


"""
██████   ██████  ████████         ██ ███    ██ ██ ████████ 
██   ██ ██    ██    ██            ██ ████   ██ ██    ██    
██████  ██    ██    ██            ██ ██ ██  ██ ██    ██    
██   ██ ██    ██    ██            ██ ██  ██ ██ ██    ██    
██████   ██████     ██    ███████ ██ ██   ████ ██    ██    
Start the pubsub client for the Twitch channel
"""

BOT_CONFIG = bot_config.BotConfig().get_bot_config()
dynamodb = boto3.resource(
    "dynamodb", region_name=BOT_CONFIG.get("aws").get("region_name")
)
user_table = dynamodb.Table("MSecBot_User")
ec2 = boto3.client("ec2", region_name=BOT_CONFIG.get("aws").get("region_name"))


async def setup_bot() -> CustomBot:
    print(f"{Fore.RED}Starting TwitchRCE!{Style.RESET_ALL}")

    # init asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # fetch bot app token
    app_access_token = loop.run_until_complete(get_app_token())

    scope = (
        "user:read:chat user:write:chat moderator:read:suspicious_users moderator:read:chatters "
        "user:manage:chat_color moderator:manage:chat_messages moderator:manage:chat_settings "
        "moderator:read:chat_settings chat:read chat:edit user:read:email user:edit:broadcast "
        "user:read:broadcast clips:edit bits:read channel:moderate channel:read:subscriptions "
        "whispers:read whispers:edit moderation:read channel:read:redemptions channel:edit:commercial "
        "channel:read:hype_train channel:manage:broadcast user:edit:follows channel:manage:redemptions "
        "user:read:blocked_users user:manage:blocked_users user:read:subscriptions user:read:follows "
        "channel:manage:polls channel:manage:predictions channel:read:polls channel:read:predictions "
        "moderator:manage:automod channel:read:goals moderator:read:automod_settings "
        "moderator:manage:banned_users moderator:read:blocked_terms moderator:manage:blocked_terms "
        "channel:manage:raids moderator:manage:announcements channel:read:vips channel:manage:vips "
        "user:manage:whispers channel:read:charity moderator:read:shield_mode moderator:manage:shield_mode "
        "moderator:read:shoutouts moderator:manage:shoutouts moderator:read:followers "
        "channel:read:guest_star channel:manage:guest_star moderator:read:guest_star "
        "moderator:manage:guest_star channel:bot user:bot channel:read:ads user:read:moderated_channels "
        "user:read:emotes moderator:read:unban_requests moderator:manage:unban_requests channel:read:editors "
        "analytics:read:games analytics:read:extensions"
    )
    api_gateway_invoke_url = (
        BOT_CONFIG.get("aws").get("api_gateway").get("api_gateway_invoke_url")
    )
    api_gateway_route = (
        BOT_CONFIG.get("aws").get("api_gateway").get("api_gateway_route")
    )
    redirect_uri = f"{api_gateway_invoke_url}{api_gateway_route}"
    authorization_url = (
        f"https://id.twitch.tv/oauth2/authorize?client_id={BOT_CONFIG.get('twitch').get('client_id')}"
        f"&force_verify=true"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={scope.replace(' ', '%20')}"
        f"&state={secrets.token_hex(16)}"
    )

    # fetch bot user token (refresh it if needed)
    bot_user = None
    try:
        response = user_table.get_item(
            Key={"id": int(BOT_CONFIG.get("twitch").get("bot_user_id"))}
        )
        bot_user = response.get("Item")

        # the bot user has no twitch access token stored in db so can't use chat programmatically
        if not bot_user.get("access_token"):
            # Send URL to stdout allows the user to grant the oauth flow and store an access token in the db
            # TODO: Deduplicate code
            print(
                f"{Fore.CYAN}Bot has no access_token. Authenticate to update your token!{Style.RESET_ALL}"
            )
            print(
                f"{Fore.CYAN}Launching auth site: {Fore.MAGENTA}{authorization_url}{Fore.CYAN}.\n{Style.RESET_ALL}"
            )

            # TODO: Keep bot here / crash out until bot user has a new access token
            raise ValueError(
                "Bot has no access_token. Authenticate to update your token!"
            )

        else:
            # the bot user has a twitch access token stored in db so check its actually valid else refresh it
            loop.run_until_complete(check_valid_token(user=bot_user))

    except AttributeError:
        # database doesn't have an item for the bot_user_id provided

        # Send URL to stdout allows the user to grant the oauth flow and store an access token in the db
        # TODO: Deduplicate code
        print(
            f"{Fore.CYAN}Failed to get bot user object for {Fore.MAGENTA}{BOT_CONFIG.get('twitch').get('bot_user_id')}{Fore.CYAN}!"
            f"{Style.RESET_ALL}"
        )
        print(
            f"{Fore.CYAN}Launching auth site: {Fore.MAGENTA}{authorization_url}{Fore.CYAN}.{Style.RESET_ALL}"
        )
        raise ValueError(
            "Bot user is not in the database. Authenticate to get an access token!"
        )

    response = ec2.describe_instances(
        InstanceIds=["i-0100638f13e5451d8"]
    )  # TODO: Don't hardcode InstanceIds
    if response.get("Reservations"):
        public_url = f"https://{response.get('Reservations')[0].get('Instances')[0].get('PublicDnsName')}"
    else:
        public_url = None

    # Create a bot from your twitchapi client credentials
    bot = CustomBot(
        app_access_token=app_access_token,
        user_token=bot_user.get("access_token"),
        initial_channels=[BOT_CONFIG.get("twitch").get("bot_join_channel")],
        eventsub_public_url=public_url,
    )
    # TODO: DeprecationWarning: from_client_credentials is not suitable for Bots.
    bot.from_client_credentials(
        client_id=BOT_CONFIG.get("twitch").get("client_id"),
        client_secret=BOT_CONFIG.get("twitch").get("client_secret"),
    )

    """
    ██████  ███████  ██████ ██      ██ ███████ ███    ██ ████████         ██ ███    ██ ██ ████████ 
    ██   ██ ██      ██      ██      ██ ██      ████   ██    ██            ██ ████   ██ ██    ██    
    ██████  ███████ ██      ██      ██ █████   ██ ██  ██    ██            ██ ██ ██  ██ ██    ██    
    ██           ██ ██      ██      ██ ██      ██  ██ ██    ██            ██ ██  ██ ██ ██    ██    
    ██      ███████  ██████ ███████ ██ ███████ ██   ████    ██    ███████ ██ ██   ████ ██    ██    
    Start the pubsub client for the Twitch channel
    https://twitchio.dev/en/stable/exts/pubsub.html
    """
    response = user_table.get_item(
        Key={
            "id": int(
                BOT_CONFIG.get("twitch").get("channel").get("bot_join_channel_id")
            )
        }
    )
    channel_user = response.get("Item")
    if channel_user:
        bot.loop.run_until_complete(
            bot.__psclient_init__(
                user_token=channel_user.get("access_token"),
                channel_id=int(channel_user.get("id")),
            )
        )

    """
    ███████ ███████  ██████ ██      ██ ███████ ███    ██ ████████         ██ ███    ██ ██ ████████ 
    ██      ██      ██      ██      ██ ██      ████   ██    ██            ██ ████   ██ ██    ██    
    █████   ███████ ██      ██      ██ █████   ██ ██  ██    ██            ██ ██ ██  ██ ██    ██    
    ██           ██ ██      ██      ██ ██      ██  ██ ██    ██            ██ ██  ██ ██ ██    ██    
    ███████ ███████  ██████ ███████ ██ ███████ ██   ████    ██    ███████ ██ ██   ████ ██    ██    
    Start the eventsub client for the Twitch channel
    https://twitchio.dev/en/stable/exts/eventsub.html
    
    """
    if public_url:
        bot.loop.run_until_complete(bot.__esclient_init__())

    """
    ██████   ██████  ████████      ██████  ██████  ███    ███ ███    ███  █████  ███    ██ ██████  ███████
    ██   ██ ██    ██    ██        ██      ██    ██ ████  ████ ████  ████ ██   ██ ████   ██ ██   ██ ██     
    ██████  ██    ██    ██        ██      ██    ██ ██ ████ ██ ██ ████ ██ ███████ ██ ██  ██ ██   ██ ███████
    ██   ██ ██    ██    ██        ██      ██    ██ ██  ██  ██ ██  ██  ██ ██   ██ ██  ██ ██ ██   ██      ██
    ██████   ██████     ██         ██████  ██████  ██      ██ ██      ██ ██   ██ ██   ████ ██████  ███████
    Start the eventsub client for the Twitch channel
    https://twitchio.dev/en/stable/exts/commands.html
    """

    @bot.event()
    async def event_error(error: Exception, data: Optional[str] = None):
        print(
            f"{Fore.RED}======================================================================== \n"
            f"Event Error: '{error}'! \n"
            f"Event Data: '{data}'! \n"
            f"======================================================================={Style.RESET_ALL}"
        )

    @bot.event()
    async def event_channel_join_failure(channel: str):
        print(
            f"{Fore.RED}Bot failed to join {Fore.MAGENTA}{channel}{Fore.RED} channel!{Style.RESET_ALL}"
        )
        bot._http.app_token = bot._http.token
        await bot.join_channels(list(channel))

    @bot.event()
    async def event_channel_joined(channel):
        print(
            f"{Fore.RED}Bot successfully joined {Fore.MAGENTA}{channel}{Fore.RED}!{Style.RESET_ALL}"
        )
        print(
            f"{Fore.RED}Connected_channels: {Fore.MAGENTA}{bot.connected_channels}{Fore.RED}!{Style.RESET_ALL}"
        )
        # Side effect of joining channel it should start listening to event subscriptions
        broadcasters: List[User] = await bot.fetch_users(names=[channel.name])
        await bot.delete_event_subscriptions(broadcasters)
        await bot.subscribe_channel_events(broadcasters)

    @bot.event()
    async def event_join(channel, user):
        print(
            f"JOIN is received from Twitch for user {user.name} in channel {channel}!"
        )
        pass

    @bot.event()
    async def event_part(user):
        print(f"PART is received from Twitch for {user.name} channel!")
        pass

    @bot.event()
    async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
        # Log redemption request - reward: CustomReward, user: PartialUser
        print(
            f"{Fore.RED}[PubSub][ChannelPoints]: {event.reward.id}, {event.reward.title}, {event.reward.cost} | "
            f"User: {event.user.id}, {event.user.name}{Style.RESET_ALL}"
        )

        # Check if reward can be redeemed at this time
        if not event.reward.paused and event.reward.enabled:
            """We have to check redemption names as id's are randomly allocated when redemption is added"""

            if event.reward.title == "Kill My Shell":
                # noinspection PyTypeChecker
                rce_cog: RCECog = bot.cogs["RCECog"]
                await rce_cog.killmyshell(
                    broadcaster_id=event.channel_id,
                    author_login=event.user.name,
                    event=event,
                )

            if event.reward.title == "VIP":
                # noinspection PyTypeChecker
                vip_cog: VIPCog = bot.cogs["VIPCog"]
                await vip_cog.add_channel_vip(
                    channel_id=event.channel_id,
                    author_id=event.user.id,
                    author_login=event.user.name,
                    event=event,
                )

    @bot.event()
    async def event_eventsub_notification_followV2(
        payload: eventsub.NotificationEvent,
    ) -> None:
        """event triggered when someone follows the channel"""
        print(
            f"{Fore.RED}[{payload.data.broadcaster.name}]{Fore.BLUE}[Follow]{Fore.RED}[EventSub]: "
            f"{payload.data.user.name} [{payload.data.user.id}]{Style.RESET_ALL}"
        )
        await bot.get_channel(payload.data.broadcaster.name).send(
            f"Thank you {payload.data.user.name} for following the channel!"
        )

    @bot.event()
    async def event_eventsub_notification_cheer(
        payload: eventsub.NotificationEvent,
    ) -> None:
        """event triggered when someone cheers in the channel"""
        if hasattr(payload.data, "is_anonymous") and payload.data.is_anonymous:
            event_string = (
                f"Received cheer event from anonymous, "
                f"cheered {payload.data.bits} bits, "
                f"message '{payload.data.message}'."
            )
        else:
            event_string = (
                f"Received cheer event from {payload.data.user.name} [{payload.data.user.id}], "
                f"cheered {payload.data.bits} bits, "
                f"message '{payload.data.message}'."
            )
        print(
            f"{Fore.RED}[{payload.data.broadcaster.name}]{Fore.BLUE}[Cheer]{Fore.RED}[EventSub]: "
            f"{event_string}{Style.RESET_ALL}"
        )

        # create stream marker (Stream markers cannot be created when the channel is offline)
        await bot.set_stream_marker(payload=payload, event_string=event_string)

        # react to event
        if hasattr(payload.data, "is_anonymous") and not payload.data.is_anonymous:
            # Get cheerer info
            channel = await bot._http.get_channels(broadcaster_id=payload.data.user.id)
            clips = await bot._http.get_clips(broadcaster_id=payload.data.user.id)
            # Acknowledge raid and reply with a channel bio
            await bot.get_channel(
                BOT_CONFIG.get("twitch").get("bot_join_channel")
            ).send(
                f"Thank you @{channel[0]['broadcaster_login']} for cheering {payload.data.bits} bits!"
            )
            # shoutout the subscriber
            if len(clips) >= 1:
                """check if sub is a streamer with clips on their channel and shoutout with clip player"""
                await bot.get_channel(payload.data.broadcaster.name).send(
                    f"!so {channel[0]['broadcaster_login']}"
                )
                await bot.announce_shoutout(
                    ctx=None,
                    broadcaster=payload.data.broadcaster,
                    channel=channel[0],
                    color="green",
                )
            else:
                """shoutout without clip player"""
                await bot.announce_shoutout(
                    ctx=None,
                    broadcaster=payload.data.broadcaster,
                    channel=channel[0],
                    color="green",
                )

    @bot.event()
    async def event_eventsub_notification_subscription(
        payload: eventsub.NotificationEvent,
    ) -> None:
        # Check if sub is gifted
        if not payload.data.is_gift:
            """event triggered when someone subscribes the channel"""
            if hasattr(payload.data, "is_anonymous") and payload.data.is_anonymous:
                event_string = (
                    f"Received subscription event from anonymous, "
                    f"with tier {payload.data.tier / 1000} sub."
                )
            else:
                event_string = (
                    f"Received subscription event from {payload.data.user.name} [{payload.data.user.id}], "
                    f"with tier {payload.data.tier / 1000} sub."
                )
            print(
                f"{Fore.RED}[{payload.data.broadcaster.name}]{Fore.BLUE}[Sub]{Fore.RED}[EventSub]: "
                f"{event_string}{Style.RESET_ALL}"
            )

            # create stream marker (Stream markers cannot be created when the channel is offline)
            await bot.set_stream_marker(payload=payload, event_string=event_string)

            # Get subscriber info
            channel = await bot._http.get_channels(broadcaster_id=payload.data.user.id)
            # Acknowledge raid and reply with a channel bio
            if len(channel) >= 1:
                try:
                    await bot.get_channel(
                        BOT_CONFIG.get("twitch").get("bot_join_channel")
                    ).send(
                        f"Thank you @{channel[0]['broadcaster_login']} for the tier {payload.data.tier / 1000} "
                        f"subscription!"
                    )
                except (
                    AttributeError
                ):  # AttributeError: 'NoneType' object has no attribute 'send'
                    pass
            # shoutout the subscriber
            clips = await bot._http.get_clips(broadcaster_id=payload.data.user.id)
            if len(clips) >= 1:
                """check if sub is a streamer with clips on their channel and shoutout with clip player"""
                await bot.get_channel(
                    BOT_CONFIG.get("twitch").get("bot_join_channel")
                ).send(f"!so {channel[0]['broadcaster_login']}")
                await bot.announce_shoutout(
                    ctx=None,
                    broadcaster=payload.data.broadcaster,
                    channel=channel[0],
                    color="green",
                )
            else:
                """shoutout without clip player"""
                await bot.announce_shoutout(
                    ctx=None,
                    broadcaster=payload.data.broadcaster,
                    channel=channel[0],
                    color="green",
                )

        else:
            """event triggered when someone gifts a sub to someone in the channel"""
            if hasattr(payload.data, "is_anonymous") and payload.data.is_anonymous:
                event_string = (
                    f"Received gift subscription event from anonymous, "
                    f"with tier {int(payload.data.tier / 1000)} sub. [GIFTED]"
                )
            else:
                event_string = (
                    f"Received gift subscription event from {payload.data.user.name} "
                    f"[{payload.data.user.id}], with tier {int(payload.data.tier / 1000)} sub. [GIFTED]"
                )
            print(
                f"{Fore.RED}[{payload.data.broadcaster.name}]{Fore.BLUE}[GiftSub]{Fore.RED}[EventSub]: "
                f"{event_string}{Style.RESET_ALL}"
            )

            # create stream marker (Stream markers cannot be created when the channel is offline)
            await bot.set_stream_marker(payload=payload, event_string=event_string)

            # Get subscriber info
            channel = await bot._http.get_channels(broadcaster_id=payload.data.user.id)
            # Acknowledge raid and reply with a channel bio
            if len(channel) >= 1:
                try:
                    await bot.get_channel(
                        BOT_CONFIG.get("twitch").get("bot_join_channel")
                    ).send(
                        f"Congratulations @{channel[0]['broadcaster_login']} on receiving a "
                        f"gifted tier {int(payload.data.tier / 1000)} subscription!"
                    )
                except (
                    AttributeError
                ):  # AttributeError: 'NoneType' object has no attribute 'send'
                    pass

    @bot.event()
    async def event_eventsub_notification_raid(
        payload: eventsub.NotificationEvent,
    ) -> None:
        """event triggered when someone raids the channel"""
        event_string = (
            f"Received raid event from {payload.data.raider.name} [{payload.data.raider.id}], "
            f"with {payload.data.viewer_count} viewers"
        )
        print(
            f"{Fore.RED}[{payload.data.reciever.name}]{Fore.BLUE}[Raid]{Fore.RED}[EventSub]: "
            f"{event_string}{Style.RESET_ALL}"
        )

        # Log the raid occurrence
        # TODO: Replace with dynamodb
        # db.insert_raid_data(raider_id=payload.data.raider.id, raider_login=payload.data.raider.name,
        #                     receiver_id=payload.data.reciever.id, receiver_login=payload.data.reciever.name,
        #                     viewer_count=payload.data.viewer_count)
        # Respond to the raid
        broadcaster = list(
            filter(lambda x: x.id == payload.data.reciever.id, bot.channel_broadcasters)
        )[0]

        # create stream marker (Stream markers cannot be created when the channel is offline)
        await bot.set_stream_marker(payload=payload, event_string=event_string)

        # Get raider info
        channel = await bot._http.get_channels(broadcaster_id=payload.data.raider.id)
        clips = await bot._http.get_clips(broadcaster_id=payload.data.raider.id)
        # Acknowledge raid and reply with a channel bio
        broadcaster_user = await bot._http.get_users(
            ids=[payload.data.reciever.id], logins=[]
        )
        await broadcaster.channel.send(
            f"TombRaid TombRaid TombRaid WELCOME RAIDERS!!! "
            f"Thank you @{channel[0]['broadcaster_login']} for trusting me with your community! "
            f"My name is {broadcaster_user[0]['display_name']}, "
            f"{broadcaster_user[0]['description']}"
        )
        # shoutout the raider
        if len(clips) >= 1:
            """check if raider is a streamer with clips on their channel and shoutout with clip player"""
            await broadcaster.channel.send(f"!so {channel[0]['broadcaster_login']}")
            await bot.announce_shoutout(
                ctx=None, broadcaster=broadcaster, channel=channel[0], color="orange"
            )
        else:
            """shoutout without clip player"""
            await bot.announce_shoutout(
                ctx=None, broadcaster=broadcaster, channel=channel[0], color="orange"
            )

    @bot.event()
    async def event_eventsub_notification_stream_start(
        payload: eventsub.NotificationEvent,
    ) -> None:
        """event triggered when stream goes live"""
        print(
            f"{Fore.RED}[{payload.data.broadcaster.name}]{Fore.BLUE}[StreamOnline]{Fore.RED}[EventSub]: "
            f"type={payload.data.type}, started_at={payload.data.started_at}.{Style.RESET_ALL}"
        )

        # Delete custom rewards before attempting to create new ones otherwise create_reward() will fail
        await bot.delete_all_custom_rewards(payload.data.broadcaster)

        # Add new custom rewards
        await bot.add_kill_my_shell_redemption_reward(payload.data.broadcaster)
        await bot.add_vip_auto_redemption_reward(payload.data.broadcaster)

        broadcaster = list(
            filter(
                lambda x: x.id == payload.data.broadcaster.id, bot.channel_broadcasters
            )
        )[0]
        await broadcaster.channel.send(f"This stream is now online!")

    @bot.event()
    async def event_eventsub_notification_stream_end(
        payload: eventsub.NotificationEvent,
    ) -> None:
        """event triggered when stream goes offline"""
        print(
            f"{Fore.RED}[{payload.data.broadcaster.name}]{Fore.BLUE}[StreamOffline]{Fore.RED}"
            f"[EventSub]: {Style.RESET_ALL}"
        )

        # Delete custom rewards before attempting to create new ones otherwise create_reward() will fail
        await bot.delete_all_custom_rewards(payload.data.broadcaster)

        broadcaster = list(
            filter(
                lambda x: x.id == payload.data.broadcaster.id, bot.channel_broadcasters
            )
        )[0]
        await broadcaster.channel.send(f"This stream is now offline!")

    @bot.event()
    async def event_eventsub_notification_channel_charity_donate(
        payload: eventsub.ChannelCharityDonationData,
    ) -> None:
        """event triggered when user donates to an active charity campaign"""
        print(
            f"{Fore.RED}[{payload.broadcaster.name}]{Fore.BLUE}[ChannelCharityDonation]{Fore.RED}"
            f"[EventSub]: {Style.RESET_ALL}"
        )

        currency_symbol = {
            "AED": "د.إ",
            "AFN": "؋",
            "ALL": "L",
            "AMD": "֏",
            "ANG": "ƒ",
            "AOA": "Kz",
            "ARS": "$",
            "AUD": "$",
            "AWG": "ƒ",
            "AZN": "₼",
            "BAM": "KM",
            "BBD": "$",
            "BDT": "৳",
            "BGN": "лв",
            "BHD": ".د.ب",
            "BIF": "FBu",
            "BMD": "$",
            "BND": "$",
            "BOB": "Bs.",
            "BRL": "R$",
            "BSD": "$",
            "BTN": "Nu.",
            "BWP": "P",
            "BYN": "Br",
            "BZD": "BZ$",
            "CAD": "$",
            "CDF": "FC",
            "CHF": "CHF",
            "CLP": "$",
            "CNY": "¥",
            "COP": "$",
            "CRC": "₡",
            "CUP": "$",
            "CVE": "$",
            "CZK": "Kč",
            "DJF": "Fdj",
            "DKK": "kr",
            "DOP": "$",
            "DZD": "د.ج",
            "EGP": "E£",
            "ERN": "Nfk",
            "ETB": "Br",
            "EUR": "€",
            "FJD": "$",
            "FKP": "£",
            "GBP": "£",
            "GEL": "₾",
            "GGP": "£",
            "GHS": "₵",
            "GIP": "£",
            "GMD": "D",
            "GNF": "FG",
            "GTQ": "Q",
            "GYD": "$",
            "HKD": "$",
            "HNL": "L",
            "HRK": "kn",
            "HTG": "G",
            "HUF": "Ft",
            "IDR": "Rp",
            "ILS": "₪",
            "IMP": "£",
            "INR": "₹",
            "IQD": "ع.د",
            "IRR": "﷼",
            "ISK": "kr",
            "JEP": "£",
            "JMD": "$",
            "JOD": "د.ا",
            "JPY": "¥",
            "KES": "KSh",
            "KGS": "сом",
            "KHR": "៛",
            "KID": "$",
            "KMF": "CF",
            "KRW": "₩",
            "KWD": "د.ك",
            "KYD": "$",
            "KZT": "₸",
            "LAK": "₭",
            "LBP": "ل.ل",
            "LKR": "₨",
            "LRD": "$",
            "LSL": "L",
            "LYD": "ل.د",
            "MAD": "د.م.",
            "MDL": "L",
            "MGA": "Ar",
            "MKD": "ден",
            "MMK": "K",
            "MNT": "₮",
            "MOP": "P",
            "MRU": "UM",
            "MUR": "₨",
            "MVR": "Rf",
            "MWK": "MK",
            "MXN": "$",
            "MYR": "RM",
            "MZN": "MT",
            "NAD": "$",
            "NGN": "₦",
            "NIO": "C$",
            "NOK": "kr",
            "NPR": "₨",
            "NZD": "$",
            "OMR": "ر.ع.",
            "PAB": "B/.",
            "PEN": "S/.",
            "PGK": "K",
            "PHP": "₱",
            "PKR": "₨",
            "PLN": "zł",
            "PYG": "₲",
            "QAR": "ر.ق",
            "RON": "lei",
            "RSD": "дин.",
            "RUB": "₽",
            "RWF": "RF",
            "SAR": "ر.س",
            "SBD": "$",
            "SCR": "₨",
            "SDG": "ج.س.",
            "SEK": "kr",
            "SGD": "$",
            "SHP": "£",
            "SLL": "Le",
            "SOS": "Sh",
            "SRD": "$",
            "SSP": "£",
            "STN": "Db",
            "SYP": "£",
            "SZL": "L",
            "THB": "฿",
            "TJS": "SM",
            "TMT": "T",
            "TND": "د.ت",
            "TOP": "T$",
            "TRY": "₺",
            "TTD": "$",
            "TVD": "$",
            "TWD": "NT$",
            "TZS": "TSh",
            "UAH": "₴",
            "UGX": "USh",
            "USD": "$",
            "UYU": "$",
            "UZS": "лв",
            "VES": "Bs.",
            "VND": "₫",
            "VUV": "VT",
            "WST": "WS$",
            "XAF": "FCFA",
            "XCD": "$",
            "XDR": "SDR",
            "XOF": "CFA",
            "XPF": "CFP",
            "YER": "﷼",
            "ZAR": "R",
            "ZMW": "ZK",
            "ZWL": "$",
        }
        donation_value = payload.donation_value / (10**payload.donation_decimal_places)

        broadcaster = list(
            filter(lambda x: x.id == payload.broadcaster.id, bot.channel_broadcasters)
        )[0]
        await broadcaster.chat_announcement(
            f"{payload.user.name} has donated {currency_symbol}{donation_value} "
            f"towards the charity fundraiser for {payload.charity_name}! Thank you! You "
            f"can learn more about the charity here: {payload.charity_website}"
        )

    return bot


if __name__ == "__main__":
    event_loop = asyncio.get_event_loop()
    bot = event_loop.run_until_complete(setup_bot())
    bot.run()
