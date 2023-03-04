import asyncio
import json
import logging
import secrets
import socket
from typing import List

from custombot import Bot
from db.database import Database
from threading_tcp_server_with_stop import ThreadingTCPServerWithStop, CodeHandler

from twitch_api_auth import TwitchApiAuth

from twitchio import PartialUser, errors
from twitchio.ext import commands, eventsub
from twitchio.http import TwitchHTTP, logger

from ngrok import NgrokClient
import settings


# init db
db = Database()
rows = db.fetch_all_user_logins()
user_logins = [row['broadcaster_login'] for row in rows]
print("Starting TwitchRCE!", user_logins)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Start a ngrok client as all inbound event subscriptions need a public facing IP address and can handle https traffic.
ngrok_client = NgrokClient(loop=loop)


async def ngrok_start() -> (str, str):
    return await ngrok_client.start()
auth_public_url, eventsub_public_url = loop.run_until_complete(ngrok_client.start())

# Create a bot from your twitch client credentials
esbot = commands.Bot.from_client_credentials(client_id=settings.CLIENT_ID,
                                             client_secret=settings.CLIENT_SECRET)

# Create an event subscription client
esclient = eventsub.EventSubClient(client=esbot,
                                   webhook_secret='some_secret_string',
                                   callback_route=f"{eventsub_public_url}")


async def get_app_token() -> str:
    twitch_api_auth = TwitchApiAuth()
    ccgf = await twitch_api_auth.client_credentials_grant_flow()
    db.insert_app_data(ccgf['access_token'], ccgf['expires_in'], ccgf['token_type'])
    print("Updated App Token!")
    return ccgf['access_token']

row = db.fetch_app_token()
app_token = ''
if len(row) < 1:
    app_token = loop.run_until_complete(get_app_token())


user_access_token_resultset = db.fetch_user_access_token_from_login('msec_bot')  # DEFINE CHATBOT USER HERE
bot = Bot(user_token=user_access_token_resultset['access_token'],
          initial_channels=['msec_bot'],  # DEFINE CHANNEL TO JOIN HERE
          db=db)
http_client: TwitchHTTP = bot._http
http_client.client_id = settings.CLIENT_ID
http_client.client_secret = settings.CLIENT_SECRET
http_client.app_token = app_token


# check for any user logins and validate their access_tokens.
# If invalid or missing then generate new tokens
async def validate_token(login: str) -> any:
    """
    test a user token and if invalid prompt user to visit a url to generate a new token
    """
    try:
        row = db.fetch_user_access_token_from_login(login)
        validate = await http_client.validate(token=row['access_token'])
        return validate
    except errors.AuthenticationError:
        # Get UserID via Authorization code grant flow
        # https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#authorization-code-grant-flow
        scope = "analytics:read:extensions analytics:read:games bits:read channel:edit:commercial channel:manage:broadcast channel:read:charity channel:manage:extensions channel:manage:moderators channel:manage:polls channel:manage:predictions channel:manage:raids channel:manage:redemptions channel:manage:schedule channel:manage:videos channel:read:editors channel:read:goals channel:read:hype_train channel:read:polls channel:read:predictions channel:read:redemptions channel:read:stream_key channel:read:subscriptions channel:read:vips channel:manage:vips clips:edit moderation:read moderator:manage:announcements moderator:manage:automod moderator:read:automod_settings moderator:manage:automod_settings moderator:manage:banned_users moderator:read:blocked_terms moderator:manage:blocked_terms moderator:manage:chat_messages moderator:read:chat_settings moderator:manage:chat_settings moderator:read:chatters moderator:read:followers moderator:read:shield_mode moderator:manage:shield_mode moderator:read:shoutouts moderator:manage:shoutouts user:edit user:edit:follows user:manage:blocked_users user:read:blocked_users user:read:broadcast user:manage:chat_color user:read:email user:read:follows user:read:subscriptions user:manage:whispers channel:moderate chat:edit chat:read whispers:read whispers:edit"
        authorization_url = f"https://id.twitch.tv/oauth2/authorize?client_id={settings.CLIENT_ID}" \
                            f"&force_verify=true" \
                            f"&redirect_uri=http://localhost:3000/auth" \
                            f"&response_type=code" \
                            f"&scope={scope.replace(' ', '%20')}" \
                            f"&state={secrets.token_hex(16)}"
        print("Launching auth site:", authorization_url)

        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        with ThreadingTCPServerWithStop(("0.0.0.0", 3000), CodeHandler) as tcpserver:
            logger.info(f"Serving on {tcpserver.server_address}...")
            tcpserver.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if tcpserver.stop is not True:
                tcpserver.stop = False
                tcpserver.serve_forever(poll_interval=0.1)
            logger.info('Server stopped')

        twitch_api_auth = TwitchApiAuth()
        auth_result = await twitch_api_auth.obtain_access_token(code=tcpserver.code,
                                                                redirect_uri='http://localhost:3000/auth')
        http_client.token = auth_result['access_token']
        users = await http_client.get_users(ids=[], logins=[], token=auth_result['access_token'])
        db.insert_user_data(broadcaster_id=users[0]['id'], broadcaster_login=users[0]['login'],
                            email=users[0]['email'], access_token=auth_result['access_token'],
                            expires_in=auth_result['expires_in'], refresh_token=auth_result['refresh_token'],
                            scope=auth_result['scope'])

for login in user_logins:
    print(f"Validating user token for {login}")
    bot.loop.run_until_complete(validate_token(login))


async def get_initial_channel_broadcasters() -> List[PartialUser]:
    """ get broadcasters objects for every """
    user_data = await http_client.get_users(token=http_client.app_token, ids=[], logins=user_logins)
    broadcasters: List[PartialUser] = []
    for user in user_data:
        broadcasters.append(await PartialUser(http=http_client, id=user['id'], name=user['login']).fetch())
    return broadcasters
channel_broadcasters: List[PartialUser] = loop.run_until_complete(get_initial_channel_broadcasters())


bot.loop.run_until_complete(bot.__esclient_init__(esclient=esclient, database=db))  # start the event subscription client


@esbot.event()
async def event_eventsub_notification_follow(payload: eventsub.NotificationEvent) -> None:
    """ event triggered when someone follows the channel """
    print(f'Received follow event! {payload.data.user.name} [{payload.data.user.id}]')
    await bot.get_channel(payload.data.broadcaster.name).send(f'Thank you {payload.data.user.name} for following the channel!')


@esbot.event()
async def kill_everyone():
    """ invoke skynet """
    pass


@esbot.event()
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
    streams = await http_client.get_streams(user_ids=[payload.data.broadcaster.id])
    if len(streams) >= 1 and streams[0].type == 'live':
        row = db.fetch_user_access_token_from_id(payload.data.broadcaster.id)
        await payload.data.broadcaster.create_marker(token=row['access_token'],
                                                     description=event_string)
    if not payload.data.is_anonymous:
        # Get cheerer info
        channel = await http_client.get_channels(broadcaster_id=payload.data.user.id)
        clips = await http_client.get_clips(broadcaster_id=payload.data.user.id)
        # Acknowledge raid and reply with a channel bio
        await bot.get_channel(payload.data.broadcaster.name).send(f"Thank you @{channel[0]['broadcaster_login']} for cheering {payload.data.bits} bits!")
        # shoutout the subscriber
        if len(clips) >= 1:
            """ check if sub is a streamer with clips on their channel and shoutout with clip player """
            await bot.get_channel(payload.data.broadcaster.name).send(f"!so {channel[0]['broadcaster_login']}")
            await shoutout(broadcaster=payload.data.broadcaster, channel=channel[0], color='green')
        else:
            """ shoutout without clip player """
            await shoutout(broadcaster=payload.data.broadcaster, channel=channel[0], color='green')


@esbot.event()
async def event_eventsub_notification_subscription(payload: eventsub.NotificationEvent) -> None:
    """ event triggered when someone subscribes the channel """
    print(f"Received subscription event from {payload.data.user.name} [{payload.data.user.id}], "
          f"with tier {payload.data.tier / 1000} sub. {'[GIFTED]' if payload.data.is_gift else ''}")
    # create stream marker (Stream markers cannot be created when the channel is offline)
    streams = await http_client.get_streams(user_ids=[payload.data.broadcaster.id])
    if len(streams) >= 1 and streams[0]['type'] == 'live':
        access_token = db.fetch_user_access_token_from_id(payload.data.broadcaster.id)
        await payload.data.broadcaster.create_marker(token=access_token,
                                                     description=f"Received subscription event from {payload.data.user.name} [{payload.data.user.id}], "
                                                                 f"with tier {payload.data.tier / 1000} sub. {'[GIFTED]' if payload.data.is_gift else ''}")
    # Get subscriber info
    channel = await http_client.get_channels(broadcaster_id=payload.data.user.id)
    clips = await http_client.get_clips(broadcaster_id=payload.data.user.id)
    # Acknowledge raid and reply with a channel bio
    if len(channel) >= 1:
        await bot.get_channel(payload.data.broadcaster.name).send(f"Thank you @{channel[0]['broadcaster_login']} for the tier {payload.data.tier / 1000} subscription!")
    # shoutout the subscriber
    if len(clips) >= 1:
        """ check if sub is a streamer with clips on their channel and shoutout with clip player """
        await bot.get_channel(payload.data.broadcaster.name).send(f"!so {channel[0]['broadcaster_login']}")
        await shoutout(broadcaster=payload.data.broadcaster, channel=channel[0], color='green')
    else:
        """ shoutout without clip player """
        await shoutout(broadcaster=payload.data.broadcaster, channel=channel[0], color='green')


@esbot.event()
async def event_eventsub_notification_raid(payload: eventsub.NotificationEvent) -> None:
    """ event triggered when someone raids the channel """
    print(f"Received raid event from {payload.data.raider.name} [{payload.data.raider.id}], "
          f"with {payload.data.viewer_count} viewers!")
    broadcaster = list(filter(lambda x: x.id == payload.data.reciever.id, channel_broadcasters))[0]
    # create stream marker (Stream markers cannot be created when the channel is offline)
    streams = await http_client.get_streams(user_ids=[payload.data.reciever.id])
    if len(streams) >= 1 and streams[0]['type'] == 'live':
        access_token = db.fetch_user_access_token_from_id(payload.data.broadcaster.id)
        await broadcaster.create_marker(token=access_token,
                                        description=f"Received raid event from {payload.data.raider.name} [{payload.data.raider.id}], "
                                                    f"with {payload.data.viewer_count} viewers!")
    # Get raider info
    channel = await http_client.get_channels(broadcaster_id=payload.data.raider.id)
    clips = await http_client.get_clips(broadcaster_id=payload.data.raider.id)
    # Acknowledge raid and reply with a channel bio
    broadcaster_user = await http_client.get_users(ids=[payload.data.reciever.id], logins=[])
    await broadcaster.channel.send(f"TombRaid TombRaid TombRaid WELCOME RAIDERS!!! "
                                   f"Thank you @{channel[0]['broadcaster_login']} for trusting me with your community! "
                                   f"My name is {broadcaster_user[0]['display_name']}, {broadcaster_user[0]['description']}")
    # shoutout the raider
    if len(clips) >= 1:
        """ check if raider is a streamer with clips on their channel and shoutout with clip player """
        await broadcaster.channel.send(f"!so {channel[0]['broadcaster_login']}")
        await shoutout(broadcaster=broadcaster, channel=channel[0], color='orange')
    else:
        """ shoutout without clip player """
        await shoutout(broadcaster=broadcaster, channel=channel[0], color='orange')


@esbot.event()
async def event_eventsub_notification_stream_start(payload: eventsub.NotificationEvent) -> None:
    """ event triggered when stream goes live """
    print(f"Received StreamOnlineData event! [broadcaster.name={payload.data.broadcaster.name}][type={payload.data.type}][started_at={payload.data.started_at}]")

    # Delete custom rewards before attempting to create new ones otherwise create_reward() will fail
    await delete_all_custom_rewards(payload.data.broadcaster)

    # Add new custom rewards
    await add_kill_my_shell_redemption_reward(payload.data.broadcaster)
    await add_vip_auto_redemption_reward(payload.data.broadcaster)

    # GET THE CHANNEL DATA BECAUSE TWITCHIO IS A PIECE OF FUCKING SHIT
    channel = await http_client.get_channels(broadcaster_id=payload.data.broadcaster.id)
    await channel.send(f'This stream is now online!')


async def add_kill_my_shell_redemption_reward(broadcaster: PartialUser):
    """ Adds channel point redemption that immediately closes the last terminal window that was opened without warning """
    channel = await http_client.get_channels(broadcaster_id=broadcaster.id)
    if channel[0]['game_id'] in [509670, 1469308723]:  # Science & Technology, Software and Game Development
        row = db.fetch_user_access_token_from_id(broadcaster.id)
        await http_client.create_reward(broadcaster_id=broadcaster.id,
                                        title="Kill My Shell",
                                        cost=6666,
                                        prompt="Immediately closes the last terminal window that was opened without warning!",
                                        global_cooldown=5 * 60,
                                        token=row['access_token'])


async def add_vip_auto_redemption_reward(broadcaster: PartialUser):
    """ Adds channel point redemption that adds the user to the VIP list automatically """
    row = db.fetch_user_access_token_from_id(broadcaster.id)
    vips = await http_client.get_channel_vips(token=row['access_token'],
                                              broadcaster_id=broadcaster.id,
                                              first=100)
    if len(vips) < settings.MAX_VIP_SLOTS:
        access_token = db.fetch_user_access_token_from_id(broadcaster.id)
        await http_client.create_reward(broadcaster_id=broadcaster.id,
                                        title="VIP",
                                        cost=80085,
                                        prompt="VIPs have the ability to equip a special chat badge and chat in slow, sub-only, or follower-only modes!",
                                        max_per_user=1,
                                        global_cooldown=5 * 60,
                                        token=row['access_token'])


async def delete_all_custom_rewards(broadcaster: PartialUser):
    """ deletes all custom rewards (API limits deletes to those created by the bot)
        Requires a user access token that includes the channel:manage:redemptions scope. """
    row = db.fetch_user_access_token_from_id(broadcaster.id)
    rewards = await http_client.get_rewards(broadcaster_id=broadcaster.id,
                                            only_manageable=True,
                                            token=row['access_token'])
    print(f"Got rewards: [{json.dumps(rewards)}]")
    if rewards is not None:
        custom_reward_titles = ["Kill My Shell", "VIP"]
        for reward in list(filter(lambda x: x["title"] in custom_reward_titles, rewards)):
            await http_client.delete_custom_reward(broadcaster_id=broadcaster.id,
                                                   reward_id=reward["id"],
                                                   token=row['access_token'])
            print(f"Deleted reward: [id={reward['id']}][title={reward['title']}]")


async def shoutout(broadcaster: PartialUser, channel: any, color: str):
    """ Post a shoutout announcement to chat; color = blue, green, orange, purple, or primary """
    # TODO: handle blank game_name
    row = db.fetch_user_access_token_from_id(broadcaster.id)
    await http_client.post_chat_announcement(token=row['access_token'],
                                             broadcaster_id=broadcaster.id,
                                             message=f"Please check out {channel['broadcaster_name']}\'s channel https://www.twitch.tv/{channel['broadcaster_login']}! "
                                                     f"They were last playing \'{channel['game_name']}\'.",
                                             moderator_id=broadcaster.id,  # This ID must match the user ID in the user access token.
                                             color=color)  # blue green orange purple primary
    """ Perform a Twitch Shoutout command (https://help.twitch.tv/s/article/shoutouts?language=en_US). 
        The channel giving a Shoutout must be live. """
    streams = await http_client.get_streams(user_ids=[broadcaster.id])
    if len(streams) >= 1 and streams[0]['type'] == 'live':
        await broadcaster.shoutout(token=row['access_token'],
                                   to_broadcaster_id=channel['broadcaster_id'],
                                   moderator_id=broadcaster.id)


# TODO: add chatgpt commands https://github.com/openai/openai-python
# TODO: add some discord commands https://discordpy.readthedocs.io/en/stable/


bot.run()

db.backup_to_disk()
db.close()
