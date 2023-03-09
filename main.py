import asyncio

import twitchio
from twitchio.ext import eventsub, pubsub, commands
from twitchio.ext.commands import Cog, Context

from cogs.rce import RCECog
from cogs.vip import VIPCog
from custom_bot import Bot
from db.database import Database

from twitch_api_auth import TwitchApiAuth

from twitchio import errors

from ngrok import NgrokClient
import settings


# init db
db = Database()
print("Starting TwitchRCE!")
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Start a ngrok client as all inbound event subscriptions need a public facing IP address and can handle https traffic.
ngrok_client = NgrokClient(loop=loop)


async def ngrok_start() -> (str, str):
    return await ngrok_client.start()
auth_public_url, eventsub_public_url = loop.run_until_complete(ngrok_client.start())


async def get_app_token() -> str:
    """ Uses the bots client id and secret to generate a new application token via client credentials grant flow """
    twitch_api_auth = TwitchApiAuth()
    ccgf = await twitch_api_auth.client_credentials_grant_flow()
    db.insert_app_data(ccgf['access_token'], ccgf['expires_in'], ccgf['token_type'])
    print("Updated App Token!")
    return ccgf['access_token']

app_access_token_resultset = db.fetch_app_token()
app_access_token = [row['access_token'] for row in app_access_token_resultset][0]
if len(app_access_token_resultset) < 1:
    app_access_token = loop.run_until_complete(get_app_token())

user_data = [row for row in db.fetch_user_from_login(settings.BOT_USERNAME)][0]
user_access_token = user_data['access_token']
user_refresh_token = user_data['refresh_token']

# Create a bot from your twitch client credentials
bot = Bot(user_token=user_access_token,
          initial_channels=[settings.BOT_USERNAME, 'msec'],
          eventsub_public_url=eventsub_public_url,
          database=db)
bot.from_client_credentials(client_id=settings.CLIENT_ID,
                            client_secret=settings.CLIENT_SECRET)
bot._http.client_id = settings.CLIENT_ID
bot._http.client_secret = settings.CLIENT_SECRET
bot._http.app_token = app_access_token


async def refresh_user_token(user: any):
    twitch_api_auth_http = TwitchApiAuth()
    auth_result = await twitch_api_auth_http.refresh_access_token(refresh_token=user['refresh_token'])
    db.insert_user_data(user['broadcaster_id'], user['broadcaster_login'], user['email'],
                        auth_result['access_token'], auth_result['expires_in'],
                        auth_result['refresh_token'], auth_result['scope'])
    print(f"Updated access and refresh token for {user['broadcaster_login']}")
    return auth_result

try:
    """ Try to authenticate the bot with the stored bot user token """
    loop.run_until_complete(bot.__validate__(user_token=user_access_token))
except errors.AuthenticationError:
    """ Try to refresh the bot user token """
    user_access_token = bot.loop.run_until_complete(refresh_user_token(user=user_data))['access_token']
    loop.run_until_complete(bot.__validate__(user_token=user_access_token))

bot.loop.run_until_complete(bot.__channel_broadcasters_init__())  # preload broadcasters objects

user_access_token_resultset = [row for row in db.fetch_user_from_login('msec')][0]
bot.loop.run_until_complete(bot.__psclient_init__(user_token=user_access_token_resultset['access_token'],
                                                  channel_id=int(user_access_token_resultset['broadcaster_id'])))  # start the pub subscription client

bot.loop.run_until_complete(bot.__esclient_init__())  # start the event subscription client


@bot.event()
async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
    # Log redemption request - reward: CustomReward, user: PartialUser
    print(f"======================================================================== \n"
          f"Event: {event.channel_id}, {event.id}, {event.status}, {event.timestamp} \n"
          f"Reward: {event.reward.id}, {event.reward.title}, {event.reward.cost} \n"
          f"User: {event.user.id}, {event.user.name} \n"
          f"========================================================================")

    # Check if reward can be redeemed at this time
    if not event.reward.paused and event.reward.in_stock and event.reward.enabled:

        if event.reward.title == 'Kill My Shell':
            rce_cog: RCECog = bot.cogs['RCECog']
            await rce_cog.killmyshell(broadcaster_id=event.channel_id, author_login=event.user.name, event=event)

        # TODO: respond to VIP redemption
        if event.reward.title == 'VIP':
            vip_cog: VIPCog = bot.cogs['VIPCog']
            await vip_cog.add_channel_vip(channel_id=event.channel_id, author_id=event.user.id, author_login=event.user.name, event=event)


@bot.event()
async def event_eventsub_notification_follow(payload: eventsub.NotificationEvent) -> None:
    """ event triggered when someone follows the channel """
    print(f'Received follow event! {payload.data.user.name} [{payload.data.user.id}]')
    await bot.get_channel(payload.data.broadcaster.name).send(
        f'Thank you {payload.data.user.name} for following the channel!')


@bot.event()
async def event_eventsub_notification_cheer(payload: eventsub.NotificationEvent) -> None:
    """ event triggered when someone cheers in the channel """
    event_string = ""
    if payload.data.is_anonymous:
        event_string = f"Received cheer event from anonymous, " \
                       f"cheered {payload.data.bits} bits, " \
                       f"message '{payload.data.message}'."
    else:
        event_string = f"Received cheer event from {payload.data.user.name} [{payload.data.user.id}], " \
                       f"cheered {payload.data.bits} bits, " \
                       f"message '{payload.data.message}'."
    print(event_string)
    # create stream marker (Stream markers cannot be created when the channel is offline)
    streams = await bot._http.get_streams(user_ids=[payload.data.broadcaster.id])
    if len(streams) >= 1 and streams[0].type == 'live':
        access_token_resultset = bot.database.fetch_user_access_token_from_id(payload.data.reciever.id)
        access_token = [str(token) for token in access_token_resultset][0]
        await payload.data.broadcaster.create_marker(token=access_token,
                                                     description=event_string)
    if not payload.data.is_anonymous:
        # Get cheerer info
        channel = await bot._http.get_channels(broadcaster_id=payload.data.user.id)
        clips = await bot._http.get_clips(broadcaster_id=payload.data.user.id)
        # Acknowledge raid and reply with a channel bio
        await bot.get_channel(payload.data.broadcaster.name).send(
            f"Thank you @{channel[0]['broadcaster_login']} for cheering {payload.data.bits} bits!")
        # shoutout the subscriber
        if len(clips) >= 1:
            """ check if sub is a streamer with clips on their channel and shoutout with clip player """
            await bot.get_channel(payload.data.broadcaster.name).send(f"!so {channel[0]['broadcaster_login']}")
            await bot.announce_shoutout(broadcaster=payload.data.broadcaster, channel=channel[0], color='green')
        else:
            """ shoutout without clip player """
            await bot.announce_shoutout(broadcaster=payload.data.broadcaster, channel=channel[0], color='green')


@bot.event()
async def event_eventsub_notification_subscription(payload: eventsub.NotificationEvent) -> None:
    """ event triggered when someone subscribes the channel """
    print(f"Received subscription event from {payload.data.user.name} [{payload.data.user.id}], "
          f"with tier {payload.data.tier / 1000} sub. {'[GIFTED]' if payload.data.is_gift else ''}")
    # create stream marker (Stream markers cannot be created when the channel is offline)
    streams = await bot._http.get_streams(user_ids=[payload.data.broadcaster.id])
    if len(streams) >= 1 and streams[0]['type'] == 'live':
        access_token_resultset = bot.database.fetch_user_access_token_from_id(payload.data.reciever.id)
        access_token = [str(token) for token in access_token_resultset][0]
        await payload.data.broadcaster.create_marker(token=access_token,
                                                     description=f"Received subscription event from {payload.data.user.name} [{payload.data.user.id}], "
                                                                 f"with tier {payload.data.tier / 1000} sub. {'[GIFTED]' if payload.data.is_gift else ''}")
    # Get subscriber info
    channel = await bot._http.get_channels(broadcaster_id=payload.data.user.id)
    clips = await bot._http.get_clips(broadcaster_id=payload.data.user.id)
    # Acknowledge raid and reply with a channel bio
    if len(channel) >= 1:
        await bot.get_channel(payload.data.broadcaster.name).send(
            f"Thank you @{channel[0]['broadcaster_login']} for the tier {payload.data.tier / 1000} subscription!")
    # shoutout the subscriber
    if len(clips) >= 1:
        """ check if sub is a streamer with clips on their channel and shoutout with clip player """
        await bot.get_channel(payload.data.broadcaster.name).send(f"!so {channel[0]['broadcaster_login']}")
        await bot.announce_shoutout(broadcaster=payload.data.broadcaster, channel=channel[0], color='green')
    else:
        """ shoutout without clip player """
        await bot.announce_shoutout(broadcaster=payload.data.broadcaster, channel=channel[0], color='green')


@bot.event()
async def event_eventsub_notification_raid(payload: eventsub.NotificationEvent) -> None:
        """ event triggered when someone raids the channel """
        print(f"Received raid event from {payload.data.raider.name} [{payload.data.raider.id}], "
              f"with {payload.data.viewer_count} viewers!")
        # Log the raid occurence
        db.insert_raid_data(raider_id=payload.data.raider.id, raider_login=payload.data.raider.name,
                            receiver_id=payload.data.reciever.id, receiver_login=payload.data.reciever.name,
                            viewer_count=payload.data.viewer_count)
        # Respond to the raid
        broadcaster = list(filter(lambda x: x.id == payload.data.reciever.id, bot.channel_broadcasters))[0]
        # create stream marker (Stream markers cannot be created when the channel is offline)
        streams = await bot._http.get_streams(user_ids=[payload.data.reciever.id])
        if len(streams) >= 1 and streams[0]['type'] == 'live':
            access_token_resultset = bot.database.fetch_user_access_token_from_id(payload.data.reciever.id)
            access_token = [str(token) for token in access_token_resultset][0]
            await broadcaster.create_marker(token=access_token,
                                            description=f"Received raid event from {payload.data.raider.name} [{payload.data.raider.id}], "
                                                        f"with {payload.data.viewer_count} viewers!")
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
            await bot.announce_shoutout(broadcaster=broadcaster, channel=channel[0], color='orange')
        else:
            """ shoutout without clip player """
            await bot.announce_shoutout(broadcaster=broadcaster, channel=channel[0], color='orange')


@bot.event()
async def event_eventsub_notification_stream_start(payload: eventsub.NotificationEvent) -> None:
    """ event triggered when stream goes live """
    print(
        f"Received StreamOnlineData event! [broadcaster.name={payload.data.broadcaster.name}][type={payload.data.type}][started_at={payload.data.started_at}]")

    # Delete custom rewards before attempting to create new ones otherwise create_reward() will fail
    await bot.delete_all_custom_rewards(payload.data.broadcaster)

    # Add new custom rewards
    await bot.add_kill_my_shell_redemption_reward(payload.data.broadcaster)
    await bot.add_vip_auto_redemption_reward(payload.data.broadcaster)

    channel = await bot._http.get_channels(broadcaster_id=payload.data.broadcaster.id)
    await channel.send(f'This stream is now online!')


@bot.event()
async def event_eventsub_notification_stream_end(payload: eventsub.NotificationEvent) -> None:
        """ event triggered when stream goes offline """
        print(
            f"Received StreamOfflineData event! [broadcaster.name={payload.data.broadcaster.name}]")

        # Delete custom rewards before attempting to create new ones otherwise create_reward() will fail
        await bot.delete_all_custom_rewards(payload.data.broadcaster)

        channel = await bot._http.get_channels(broadcaster_id=payload.data.broadcaster.id)
        await channel.send(f'This stream is now offline!')

bot.run()

db.backup_to_disk()
db.close()
