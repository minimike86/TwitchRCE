import asyncio
from typing import Optional, List

from colorama import Fore, Back, Style
from twitchio import User
from twitchio.ext import eventsub, pubsub

from cogs.rce import RCECog
from cogs.vip import VIPCog
from custom_bot import Bot
from db.database import Database

from api.twitch.twitch_api_auth import TwitchApiAuth

from ngrok.ngrok import NgrokClient
import settings


print(f"{Fore.RED}Starting TwitchRCE!{Style.RESET_ALL}")

# init db
db = Database()

# init asyncio
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# init TwitchApiAuth
twitch_api_auth_http = TwitchApiAuth()


async def get_app_token() -> str:
    """ Uses the bots' client id and secret to generate a new application token via client credentials grant flow """
    client_creds_grant_flow = await twitch_api_auth_http.client_credentials_grant_flow()
    db.insert_app_data(client_creds_grant_flow['access_token'], client_creds_grant_flow['expires_in'], client_creds_grant_flow['token_type'])
    print(f"{Fore.RED}Updated App Token!{Style.RESET_ALL}")
    return client_creds_grant_flow['access_token']


async def check_valid_token(user: any) -> bool:
    is_valid_token = await twitch_api_auth_http.validate_token(access_token=user['access_token'])
    if not is_valid_token:
        access_token = await refresh_user_token(user=user)
        is_valid_token = await twitch_api_auth_http.validate_token(access_token=access_token)
    return is_valid_token


async def refresh_user_token(user: any) -> str:
    auth_result = await twitch_api_auth_http.refresh_access_token(refresh_token=user['refresh_token'])
    db.insert_user_data(user['broadcaster_id'], user['broadcaster_login'], user['email'],
                        auth_result['access_token'], auth_result['expires_in'],
                        auth_result['refresh_token'], auth_result['scope'])
    print(f"{Fore.RED}Updated access and refresh token for {Fore.MAGENTA}{user['broadcaster_login']}{Fore.RED}!{Style.RESET_ALL}")
    return auth_result['access_token']

# Start a ngrok client as all inbound event subscriptions need a public facing IP address and can handle https traffic.
ngrok_client = NgrokClient(loop=loop)


async def ngrok_start() -> (str, str):
    return await ngrok_client.start()
auth_public_url, eventsub_public_url = loop.run_until_complete(ngrok_client.start())

# fetch bot app token
# app_access_token_result_set = db.fetch_app_token()
# app_access_token = [row['access_token'] for row in app_access_token_result_set][0]
app_access_token = loop.run_until_complete(get_app_token())

# fetch bot user token (refresh it if needed)
bot_user_result_set = [row for row in db.fetch_user(broadcaster_login=settings.BOT_USERNAME)][0]
is_valid = loop.run_until_complete(check_valid_token(user=bot_user_result_set))

# Create a bot from your twitch client credentials
bot_user_result_set = [row for row in db.fetch_user(broadcaster_login=settings.BOT_USERNAME)][0]
user_access_token = bot_user_result_set['access_token']
bot = Bot(user_token=user_access_token,
          initial_channels=[settings.BOT_JOIN_CHANNEL],
          eventsub_public_url=eventsub_public_url,
          database=db)
bot.from_client_credentials(client_id=settings.CLIENT_ID,
                            client_secret=settings.CLIENT_SECRET)

bot.loop.run_until_complete(bot.__channel_broadcasters_init__())  # preload broadcasters objects

bot_join_user_result_set = [row for row in db.fetch_user(broadcaster_login=settings.BOT_JOIN_CHANNEL)][0]
bot.loop.run_until_complete(bot.__psclient_init__(user_token=bot_join_user_result_set['access_token'],
                                                  channel_id=int(bot_join_user_result_set['broadcaster_id'])))  # start the pub subscription client

bot.loop.run_until_complete(bot.__esclient_init__())  # start the event subscription client


@bot.event()
async def event_error(error: Exception, data: Optional[str] = None):
    print(f"{Fore.RED}======================================================================== \n"
          f"Event Error: '{error}'! \n"
          f"Event Data: '{data}'! \n"
          f"======================================================================={Style.RESET_ALL}")


@bot.event()
async def event_channel_join_failure(channel: str):
    print(f"{Fore.RED}Bot failed to join {Fore.MAGENTA}{channel}{Fore.RED} channel!{Style.RESET_ALL}")


@bot.event()
async def event_channel_joined(channel):
    print(f"{Fore.RED}Bot successfully joined {Fore.MAGENTA}{channel}{Fore.RED}!{Style.RESET_ALL}")
    print(f"{Fore.RED}Connected_channels: {Fore.MAGENTA}{bot.connected_channels}{Fore.RED}!{Style.RESET_ALL}")
    # Side effect of joining channel it should start listening to event subscriptions
    broadcasters: List[User] = await bot.fetch_users(names=[channel.name])
    await bot.delete_event_subscriptions(broadcasters)
    await bot.subscribe_channel_events(broadcasters)


@bot.event()
async def event_join(channel, user):
    # print(f"JOIN is received from Twitch for {channel} channel!")
    pass


@bot.event()
async def event_part(user):
    # print(f"PART is received from Twitch for {user.name} channel!")
    pass


@bot.event()
async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
    # Log redemption request - reward: CustomReward, user: PartialUser
    print(f"{Fore.RED}[PubSub][ChannelPoints]: {event.reward.id}, {event.reward.title}, {event.reward.cost} | "
          f"User: {event.user.id}, {event.user.name}{Style.RESET_ALL}")

    # Check if reward can be redeemed at this time
    if not event.reward.paused and event.reward.enabled:
        """ We have to check redemption names as id's are randomly allocated when redemption is added """

        if event.reward.title == 'Kill My Shell':
            # noinspection PyTypeChecker
            rce_cog: RCECog = bot.cogs['RCECog']
            await rce_cog.killmyshell(broadcaster_id=event.channel_id, author_login=event.user.name, event=event)

        if event.reward.title == 'VIP':
            # noinspection PyTypeChecker
            vip_cog: VIPCog = bot.cogs['VIPCog']
            await vip_cog.add_channel_vip(channel_id=event.channel_id, author_id=event.user.id, author_login=event.user.name, event=event)


@bot.event()
async def event_eventsub_notification_followV2(payload: eventsub.NotificationEvent) -> None:
    """ event triggered when someone follows the channel """
    print(f"{Fore.RED}[{payload.data.broadcaster.name}]{Fore.BLUE}[Follow]{Fore.RED}[EventSub]: "
          f"{payload.data.user.name} [{payload.data.user.id}]{Style.RESET_ALL}")
    await bot.get_channel(payload.data.broadcaster.name).send(
        f'Thank you {payload.data.user.name} for following the channel!')


@bot.event()
async def event_eventsub_notification_cheer(payload: eventsub.NotificationEvent) -> None:
    """ event triggered when someone cheers in the channel """
    if hasattr(payload.data, 'is_anonymous') and payload.data.is_anonymous:
        event_string = f"Received cheer event from anonymous, " \
                       f"cheered {payload.data.bits} bits, " \
                       f"message '{payload.data.message}'."
    else:
        event_string = f"Received cheer event from {payload.data.user.name} [{payload.data.user.id}], " \
                       f"cheered {payload.data.bits} bits, " \
                       f"message '{payload.data.message}'."
    print(f"{Fore.RED}[{payload.data.broadcaster.name}]{Fore.BLUE}[Cheer]{Fore.RED}[EventSub]: "
          f"{event_string}{Style.RESET_ALL}")

    # create stream marker (Stream markers cannot be created when the channel is offline)
    await bot.set_stream_marker(payload=payload, event_string=event_string)

    # react to event
    if hasattr(payload.data, 'is_anonymous') and not payload.data.is_anonymous:
        # Get cheerer info
        channel = await bot._http.get_channels(broadcaster_id=payload.data.user.id)
        clips = await bot._http.get_clips(broadcaster_id=payload.data.user.id)
        # Acknowledge raid and reply with a channel bio
        await bot.get_channel(settings.BOT_JOIN_CHANNEL).send(
            f"Thank you @{channel[0]['broadcaster_login']} for cheering {payload.data.bits} bits!")
        # shoutout the subscriber
        if len(clips) >= 1:
            """ check if sub is a streamer with clips on their channel and shoutout with clip player """
            await bot.get_channel(payload.data.broadcaster.name).send(f"!so {channel[0]['broadcaster_login']}")
            await bot.announce_shoutout(ctx=None, broadcaster=payload.data.broadcaster, channel=channel[0], color='green')
        else:
            """ shoutout without clip player """
            await bot.announce_shoutout(ctx=None, broadcaster=payload.data.broadcaster, channel=channel[0], color='green')


@bot.event()
async def event_eventsub_notification_subscription(payload: eventsub.NotificationEvent) -> None:
    # Check if sub is gifted
    if not payload.data.is_gift:
        """ event triggered when someone subscribes the channel """
        if hasattr(payload.data, 'is_anonymous') and payload.data.is_anonymous:
            event_string = f"Received subscription event from anonymous, " \
                           f"with tier {payload.data.tier / 1000} sub."
        else:
            event_string = f"Received subscription event from {payload.data.user.name} [{payload.data.user.id}], " \
                           f"with tier {payload.data.tier / 1000} sub."
        print(f"{Fore.RED}[{payload.data.broadcaster.name}]{Fore.BLUE}[Sub]{Fore.RED}[EventSub]: "
              f"{event_string}{Style.RESET_ALL}")

        # create stream marker (Stream markers cannot be created when the channel is offline)
        await bot.set_stream_marker(payload=payload, event_string=event_string)

        # Get subscriber info
        channel = await bot._http.get_channels(broadcaster_id=payload.data.user.id)
        # Acknowledge raid and reply with a channel bio
        if len(channel) >= 1:
            try:
                await bot.get_channel(settings.BOT_JOIN_CHANNEL).send(
                    f"Thank you @{channel[0]['broadcaster_login']} for the tier {payload.data.tier / 1000} subscription!")
            except AttributeError:  # AttributeError: 'NoneType' object has no attribute 'send'
                pass
        # shoutout the subscriber
        clips = await bot._http.get_clips(broadcaster_id=payload.data.user.id)
        if len(clips) >= 1:
            """ check if sub is a streamer with clips on their channel and shoutout with clip player """
            await bot.get_channel(settings.BOT_JOIN_CHANNEL).send(f"!so {channel[0]['broadcaster_login']}")
            await bot.announce_shoutout(ctx=None, broadcaster=payload.data.broadcaster, channel=channel[0], color='green')
        else:
            """ shoutout without clip player """
            await bot.announce_shoutout(ctx=None, broadcaster=payload.data.broadcaster, channel=channel[0], color='green')

    else:
        """ event triggered when someone gifts a sub to someone in the channel """
        if hasattr(payload.data, 'is_anonymous') and payload.data.is_anonymous:
            event_string = f"Received gift subscription event from anonymous, " \
                           f"with tier {int(payload.data.tier / 1000)} sub. [GIFTED]"
        else:
            event_string = f"Received gift subscription event from {payload.data.user.name} [{payload.data.user.id}], " \
                           f"with tier {int(payload.data.tier / 1000)} sub. [GIFTED]"
        print(f"{Fore.RED}[{payload.data.broadcaster.name}]{Fore.BLUE}[GiftSub]{Fore.RED}[EventSub]: "
              f"{event_string}{Style.RESET_ALL}")

        # create stream marker (Stream markers cannot be created when the channel is offline)
        await bot.set_stream_marker(payload=payload, event_string=event_string)

        # Get subscriber info
        channel = await bot._http.get_channels(broadcaster_id=payload.data.user.id)
        # Acknowledge raid and reply with a channel bio
        if len(channel) >= 1:
            try:
                await bot.get_channel(settings.BOT_JOIN_CHANNEL).send(
                    f"Congratulations @{channel[0]['broadcaster_login']} on receiving a gifted tier {int(payload.data.tier / 1000)} subscription!")
            except AttributeError:  # AttributeError: 'NoneType' object has no attribute 'send'
                pass


@bot.event()
async def event_eventsub_notification_raid(payload: eventsub.NotificationEvent) -> None:
    """ event triggered when someone raids the channel """
    event_string = f"Received raid event from {payload.data.raider.name} [{payload.data.raider.id}], " \
                   f"with {payload.data.viewer_count} viewers"
    print(f"{Fore.RED}[{payload.data.reciever.name}]{Fore.BLUE}[Raid]{Fore.RED}[EventSub]: "
          f"{event_string}{Style.RESET_ALL}")

    # Log the raid occurrence
    db.insert_raid_data(raider_id=payload.data.raider.id, raider_login=payload.data.raider.name,
                        receiver_id=payload.data.reciever.id, receiver_login=payload.data.reciever.name,
                        viewer_count=payload.data.viewer_count)
    # Respond to the raid
    broadcaster = list(filter(lambda x: x.id == payload.data.reciever.id, bot.channel_broadcasters))[0]

    # create stream marker (Stream markers cannot be created when the channel is offline)
    await bot.set_stream_marker(payload=payload, event_string=event_string)

    # Get raider info
    channel = await bot._http.get_channels(broadcaster_id=payload.data.raider.id)
    clips = await bot._http.get_clips(broadcaster_id=payload.data.raider.id)
    # Acknowledge raid and reply with a channel bio
    broadcaster_user = await bot._http.get_users(ids=[payload.data.reciever.id], logins=[])
    await broadcaster.channel.send(f"TombRaid TombRaid TombRaid WELCOME RAIDERS!!! "
                                   f"Thank you @{channel[0]['broadcaster_login']} for trusting me with your community! "
                                   f"My name is {broadcaster_user[0]['display_name']}, {broadcaster_user[0]['description']}")
    # shoutout the raider
    if len(clips) >= 1:
        """ check if raider is a streamer with clips on their channel and shoutout with clip player """
        await broadcaster.channel.send(f"!so {channel[0]['broadcaster_login']}")
        await bot.announce_shoutout(ctx=None, broadcaster=broadcaster, channel=channel[0], color='orange')
    else:
        """ shoutout without clip player """
        await bot.announce_shoutout(ctx=None, broadcaster=broadcaster, channel=channel[0], color='orange')


@bot.event()
async def event_eventsub_notification_stream_start(payload: eventsub.NotificationEvent) -> None:
    """ event triggered when stream goes live """
    print(f"{Fore.RED}[{payload.data.broadcaster.name}]{Fore.BLUE}[StreamOnline]{Fore.RED}[EventSub]: "
          f"type={payload.data.type}, started_at={payload.data.started_at}.{Style.RESET_ALL}")

    # Delete custom rewards before attempting to create new ones otherwise create_reward() will fail
    await bot.delete_all_custom_rewards(payload.data.broadcaster)

    # Add new custom rewards
    await bot.add_kill_my_shell_redemption_reward(payload.data.broadcaster)
    await bot.add_vip_auto_redemption_reward(payload.data.broadcaster)

    broadcaster = list(filter(lambda x: x.id == payload.data.broadcaster.id, bot.channel_broadcasters))[0]
    await broadcaster.channel.send(f"This stream is now online!")


@bot.event()
async def event_eventsub_notification_stream_end(payload: eventsub.NotificationEvent) -> None:
    """ event triggered when stream goes offline """
    print(f"{Fore.RED}[{payload.data.broadcaster.name}]{Fore.BLUE}[StreamOffline]{Fore.RED}[EventSub]:{Style.RESET_ALL}")

    # Delete custom rewards before attempting to create new ones otherwise create_reward() will fail
    await bot.delete_all_custom_rewards(payload.data.broadcaster)

    broadcaster = list(filter(lambda x: x.id == payload.data.broadcaster.id, bot.channel_broadcasters))[0]
    await broadcaster.channel.send(f"This stream is now offline!")

bot.run()

db.backup_to_disk()
db.close()
