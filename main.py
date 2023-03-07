import asyncio

from custom_bot import Bot
from db.database import Database

from twitch_api_auth import TwitchApiAuth

from twitchio import errors
from twitchio.http import TwitchHTTP

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
bot.loop.run_until_complete(bot.__esclient_init__())  # start the event subscription client

bot.run()

db.backup_to_disk()
db.close()
