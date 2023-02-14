import asyncio

import twitchio
from twitchio.ext import commands, eventsub

from ngrok import ngrok, NgrokClient
import settings

print("Starting TwitchRCE!", settings.INITIAL_CHANNELS)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


ngrok_client = NgrokClient()
def start_ngrok():
    tunnels = ngrok.get_tunnels()

    async def get_ngrok_tunnels() -> (str, str):
        ngrok_auth = ngrok_client.get_auth_tunnel()
        ngrok_eventsub = ngrok_client.get_eventsub_tunnel()
        for tunnel in await ngrok_client.get_ngrok_tunnels():
            print(f"{tunnel.name}: {tunnel.public_url}")
        return ngrok_auth, ngrok_eventsub

    if len(tunnels) < 1:
        tunnels = loop.run_until_complete(get_ngrok_tunnels())

    for tunnel in tunnels:
        if str(settings.AUTH_URI_PORT) in tunnel.config['addr']:
            settings.AUTH_URI_TUNNEL_PUBLIC_URL = tunnel.public_url
        if str(settings.EVENTSUB_URI_PORT) in tunnel.config['addr']:
            settings.CALLBACK_ROUTE = f"{tunnel.public_url}{settings.EVENTSUB_URI_ENDPOINT}"
        print(f"{tunnel.public_url} -> {tunnel.config['addr']}")


start_ngrok()

esbot = commands.Bot.from_client_credentials(client_id=settings.CLIENT_ID,
                                             client_secret=settings.CLIENT_SECRET)

esclient = eventsub.EventSubClient(client=esbot,
                                   webhook_secret='some_secret_string',
                                   callback_route=settings.CALLBACK_ROUTE)


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(token=settings.CHAT_OAUTH_ACCESS_TOKEN,
                         prefix='!',
                         initial_channels=['msec'])

        # Load cogs
        from cogs.rce import RCECog
        self.add_cog(RCECog(self))
        from cogs.vip import VIPCog
        self.add_cog(VIPCog(self))

    async def __ainit__(self) -> None:
        try:
            print(f"Starting esclient with callback_route: {settings.CALLBACK_ROUTE} [port={settings.EVENTSUB_URI_PORT}]")
            loop.create_task(esclient.listen(port=settings.EVENTSUB_URI_PORT))
            print(f"Running EventSub server on {settings.CALLBACK_ROUTE}")
        except Exception as e:
            print(e.with_traceback(tb=None))

        try:
            await esclient.subscribe_channel_follows(broadcaster=125444292)
        except twitchio.HTTPException:
            pass

    async def event_ready(self):
        print(f'Logged into channel(s): {self.connected_channels}, as User: {self.nick} (ID: {self.user_id})')

    async def event_message(self, message: twitchio.Message):
        # Messages with echo set to True are messages sent by the bot...
        # For now, we just want to ignore them...
        if message.echo:
            return

        # Print the contents of our message to console...
        print('Bot: ', message.author.name, message.content)  # Print the contents of our message to console...

        # Since we have commands and are overriding the default `event_message`
        # We must let the bot know we want to handle and invoke our commands...
        await self.handle_commands(message)

    @commands.command()
    async def hello(self, ctx: commands.Context):
        await ctx.send(f'Hello {ctx.author.name}!')


bot = Bot()
bot.loop.run_until_complete(bot.__ainit__())


@esbot.event()
async def event_eventsub_notification_follow(payload: eventsub.ChannelFollowData) -> None:
    print('Received follow event!')
    channel = bot.get_channel('msec')
    await channel.send(f'{payload.data.user.name} followed woohoo!')

bot.run()
