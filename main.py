import asyncio
import json
from typing import Collection

import twitchio
from twitchio import PartialUser
from twitchio.ext import commands, eventsub
from twitchio.ext.eventsub import StreamOnlineData
from twitchio.http import TwitchHTTP

from ngrok import NgrokClient
import settings

print("Starting TwitchRCE!", settings.INITIAL_CHANNELS)
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

# Custom bot class
class Bot(commands.Bot):
    def __init__(self):
        super().__init__(token=settings.USER_TOKEN,
                         prefix='!',
                         initial_channels=['msec'])

        # Load cogs
        from cogs.rce import RCECog
        self.add_cog(RCECog(self))
        from cogs.vip import VIPCog
        self.add_cog(VIPCog(self))

    async def __ainit__(self) -> None:
        try:
            print(f"Starting esclient...")
            loop.create_task(esclient.listen(port=settings.EVENTSUB_URI_PORT))
            print(f"Running EventSub server on [port={settings.EVENTSUB_URI_PORT}]")
        except Exception as e:
            print(e.with_traceback(tb=None))

        try:
            await esclient.subscribe_channel_follows(broadcaster=125444292)
        except twitchio.HTTPException:
            pass

        try:
            await esclient.subscribe_channel_stream_start(broadcaster=125444292)
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

# init custom bot
bot = Bot()
bot.loop.run_until_complete(bot.__ainit__())

# authenticate bots TwitchHTTP client
http_client: TwitchHTTP = bot._http
http_client.client_id = settings.CLIENT_ID
http_client.token = settings.USER_TOKEN

# get broadcasters User object
async def get_broadcaster_user() -> PartialUser:
    users = await http_client.get_users(token=settings.USER_TOKEN, ids=[], logins=settings.INITIAL_CHANNELS)
    user_data = list(filter(lambda x: x['login'] in settings.INITIAL_CHANNELS, users))[0]
    return PartialUser(http=http_client, id=user_data['id'], name=user_data['login'])
broadcaster: PartialUser = loop.run_until_complete(get_broadcaster_user())

@esbot.event()
async def event_eventsub_notification_follow(payload: eventsub.ChannelFollowData) -> None:
    print('Received follow event!')
    channel = bot.get_channel('msec')
    await channel.send(f'{payload.data.user.name} followed woohoo!')


async def delete_all_custom_rewards(rewards: Collection, custom_reward_titles: Collection):
    if rewards is not None:
        for reward in list(filter(lambda x: x["title"] in custom_reward_titles, rewards)):
            await http_client.delete_custom_reward(broadcaster_id=broadcaster.id,
                                                   reward_id=reward["id"],
                                                   token=settings.USER_TOKEN)
            print(f"Deleted reward: [id={reward['id']}][title={reward['title']}]")


@esbot.event()
async def event_eventsub_notification_stream_start(payload: StreamOnlineData) -> None:
    print(f"Received StreamOnlineData event! [broadcaster.name={payload.data.broadcaster.name}][type={payload.data.type}][started_at={payload.data.started_at}]")

    # Delete custom rewards before attempting to create new ones otherwise create_reward() will fail
    custom_reward_titles = ["Kill My Shell", "VIP"]
    rewards = await http_client.get_rewards(broadcaster_id=broadcaster.id,
                                            only_manageable=True,
                                            token=settings.USER_TOKEN)
    print(f"Got rewards: [{json.dumps(rewards)}]")
    await delete_all_custom_rewards(rewards, custom_reward_titles)

    # TODO: if sci & tech then add kill my shell
    await http_client.create_reward(broadcaster_id=broadcaster.id,
                                    title="Kill My Shell",
                                    cost=6666,
                                    prompt="Immediately close any terminal I have open without warning!",
                                    global_cooldown=5 * 60,
                                    token=settings.USER_TOKEN)

    # TODO: check for free VIP slots before added
    await http_client.create_reward(broadcaster_id=broadcaster.id,
                                    title="VIP",
                                    cost=80085,
                                    prompt="VIPs have the ability to equip a special chat badge and chat in slow, sub-only, or follower-only modes!",
                                    global_cooldown=5 * 60,
                                    token=settings.USER_TOKEN)

    await broadcaster.channel.send(f'This stream is now online!')

bot.run()
