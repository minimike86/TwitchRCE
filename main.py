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


class Bot(commands.Bot):
    """ Custom twitchio bot class """
    def __init__(self):
        super().__init__(token=settings.USER_TOKEN,
                         prefix='!',
                         initial_channels=settings.INITIAL_CHANNELS)

        """ load commands from cogs """
        # TODO: fix allow list that 0xtib3rius bypassed :)
        # from cogs.rce import RCECog  # disabled as 0xtib3rius bypassed allow list lol
        # self.add_cog(RCECog(self))  # disabled as 0xtib3rius bypassed allow list lol

        from cogs.vip import VIPCog
        self.add_cog(VIPCog(self))

    async def __esclient_init__(self) -> None:
        """ start the esclient listening on specified port """
        try:
            loop.create_task(esclient.listen(port=settings.EVENTSUB_URI_PORT))
            print(f"Running EventSub server on [port={settings.EVENTSUB_URI_PORT}]")
        except Exception as e:
            print(e.with_traceback(tb=None))

        """ before registering new event subscriptions remove old event subs """
        # TODO: make this optional some broadcasters might have pre-configured event subs that this would delete
        es_subs = await esclient._http.get_subscriptions()
        print(f"{len(es_subs)} event subs found")
        for es_sub in es_subs:
            await esclient._http.delete_subscription(es_sub)
            print(f"deleting event sub: {es_sub.id}")
        print(f"deleted all event subs.")

        try:
            """ create new event subscription for channel_follows event"""
            await esclient.subscribe_channel_follows(broadcaster=broadcaster.id)
        except twitchio.HTTPException:
            pass

        try:
            """ create new event subscription for channel_subscriptions event """
            await esclient.subscribe_channel_subscriptions(broadcaster=broadcaster.id)
        except twitchio.HTTPException:
            pass

        try:
            """ create new event subscription for channel_raid event """
            await esclient.subscribe_channel_raid(to_broadcaster=broadcaster.id)
        except twitchio.HTTPException:
            pass

        try:
            """ create new event subscription for channel_stream_start event """
            await esclient.subscribe_channel_stream_start(broadcaster=broadcaster.id)
        except twitchio.HTTPException:
            pass

    async def event_ready(self):
        """ Bot is logged into IRC and ready to do its thing. """
        print(f'Logged into channel(s): {self.connected_channels}, as User: {self.nick} (ID: {self.user_id})')

    async def event_message(self, message: twitchio.Message):
        """ Messages with echo set to True are messages sent by the bot. ignore them. """
        if message.echo:
            return
        print('Bot: ', message.author.name, message.content)  # Print the contents of our message to console...
        await self.handle_commands(message)  # we have commands overriding the default `event_message`

    @commands.command()
    async def hello(self, ctx: commands.Context):
        """ type !hello to say hello to author """
        await ctx.send(f'Hello {ctx.author.name}!')


bot = Bot()
http_client: TwitchHTTP = bot._http  # authenticate bots TwitchHTTP client
http_client.client_id = settings.CLIENT_ID
http_client.token = settings.USER_TOKEN


async def get_broadcaster_user() -> PartialUser:
    """ get broadcasters User object """
    users = await http_client.get_users(token=settings.USER_TOKEN, ids=[], logins=settings.INITIAL_CHANNELS)
    user_data = list(filter(lambda x: x['login'] in settings.INITIAL_CHANNELS, users))[0]
    return PartialUser(http=http_client, id=user_data['id'], name=user_data['login'])
broadcaster: PartialUser = loop.run_until_complete(get_broadcaster_user())


bot.loop.run_until_complete(bot.__esclient_init__())  # start the event subscription client


@esbot.event()
async def event_eventsub_notification_follow(payload: eventsub.ChannelFollowData) -> None:
    """ event triggered when someone follows the channel """
    print(f'Received follow event! {payload.data.user.name} [{payload.data.user.id}]')
    await broadcaster.channel.send(f'Thank you {payload.data.user.name} for following the channel!')


@esbot.event()
async def event_eventsub_notification_subscription(payload: eventsub.NotificationEvent) -> None:
    """ event triggered when someone subscribes the channel """
    print(f"Received subscription event from {payload.data.user.name} [{payload.data.user.id}], "
          f"with tier {payload.data.tier / 1000} sub. {'[GIFTED]' if payload.data.is_gift else ''}")
    # create stream marker (Stream markers cannot be created when the channel is offline)
    streams = await http_client.get_streams(user_ids=[broadcaster.id])
    if len(streams) >= 1 and streams[0].type == 'live':
        await broadcaster.create_marker(token=settings.USER_TOKEN,
                                        description=f"Received subscription event from {payload.data.user.name} [{payload.data.user.id}], "
                                                    f"with tier {payload.data.tier / 1000} sub. {'[GIFTED]' if payload.data.is_gift else ''}")
    # Get subscriber info
    channel = await http_client.get_channels(broadcaster_id=payload.data.user.id)
    clips = await http_client.get_clips(broadcaster_id=payload.data.user.id)
    # Acknowledge raid and reply with a channel bio
    await broadcaster.channel.send(f"Thank you @{channel[0]['broadcaster_login']} for the tier {payload.data.tier / 1000} subscription!")
    # shoutout the subscriber
    if len(clips) >= 1:
        """ check if sub is a streamer with clips on their channel and shoutout with clip player """
        await broadcaster.channel.send(f"!so {channel[0]['broadcaster_login']}")
        await shoutout(channel=channel[0], color='green')
    else:
        """ shoutout without clip player """
        await shoutout(channel=channel[0], color='green')


@esbot.event()
async def event_eventsub_notification_raid(payload: eventsub.NotificationEvent) -> None:
    """ event triggered when someone raids the channel """
    print(f"Received raid event from {payload.data.raider.name} [{payload.data.raider.id}], "
          f"with {payload.data.viewer_count} viewers!")
    # create stream marker (Stream markers cannot be created when the channel is offline)
    streams = await http_client.get_streams(user_ids=[broadcaster.id])
    if len(streams) >= 1 and streams[0].type == 'live':
        await broadcaster.create_marker(token=settings.USER_TOKEN,
                                        description=f"Received raid event from {payload.data.raider.name} [{payload.data.raider.id}], "
                                                    f"with {payload.data.viewer_count} viewers!")
    # Get raider info
    channel = await http_client.get_channels(broadcaster_id=payload.data.raider.id)
    clips = await http_client.get_clips(broadcaster_id=payload.data.raider.id)
    # Acknowledge raid and reply with a channel bio
    broadcaster_user = await http_client.get_users(ids=[broadcaster.id], logins=[])
    await broadcaster.channel.send(f"TombRaid TombRaid TombRaid WELCOME RAIDERS!!! "
                                   f"Thank you @{channel[0]['broadcaster_login']} for trusting me with your community! "
                                   f"My name is {broadcaster_user[0]['display_name']}, {broadcaster_user[0]['description']}")
    # shoutout the raider
    if len(clips) >= 1:
        """ check if raider is a streamer with clips on their channel and shoutout with clip player """
        await broadcaster.channel.send(f"!so {channel[0]['broadcaster_login']}")
        await shoutout(channel=channel[0], color='orange')
    else:
        """ shoutout without clip player """
        await shoutout(channel=channel[0], color='orange')


@esbot.event()
async def event_eventsub_notification_stream_start(payload: StreamOnlineData) -> None:
    """ event triggered when stream goes live """
    print(f"Received StreamOnlineData event! [broadcaster.name={payload.data.broadcaster.name}][type={payload.data.type}][started_at={payload.data.started_at}]")

    # Delete custom rewards before attempting to create new ones otherwise create_reward() will fail
    await delete_all_custom_rewards()

    # Add new custom rewards
    await add_kill_my_shell_redemption_reward()
    await add_vip_auto_redemption_reward()

    await broadcaster.channel.send(f'This stream is now online!')


async def add_kill_my_shell_redemption_reward():
    """ Adds channel point redemption that immediately closes the last terminal window that was opened without warning """
    channel = await http_client.get_channels(broadcaster_id=broadcaster.id)
    if channel[0]['game_id'] in [509670, 1469308723]:  # Science & Technology, Software and Game Development
        await http_client.create_reward(broadcaster_id=broadcaster.id,
                                        title="Kill My Shell",
                                        cost=6666,
                                        prompt="Immediately closes the last terminal window that was opened without warning!",
                                        global_cooldown=5 * 60,
                                        token=settings.USER_TOKEN)


async def add_vip_auto_redemption_reward():
    """ Adds channel point redemption that adds the user to the VIP list automatically """
    vips = await http_client.get_channel_vips(token=settings.USER_TOKEN,
                                              broadcaster_id=broadcaster.id,
                                              first=100)
    if len(vips.data) < settings.MAX_VIP_SLOTS:
        await http_client.create_reward(broadcaster_id=broadcaster.id,
                                        title="VIP",
                                        cost=80085,
                                        prompt="VIPs have the ability to equip a special chat badge and chat in slow, sub-only, or follower-only modes!",
                                        max_per_user=1,
                                        global_cooldown=5 * 60,
                                        token=settings.USER_TOKEN)


async def delete_all_custom_rewards():
    """ deletes all custom rewards (API limits deletes to those created by the bot) """
    rewards = await http_client.get_rewards(broadcaster_id=broadcaster.id,
                                            only_manageable=True,
                                            token=settings.USER_TOKEN)
    print(f"Got rewards: [{json.dumps(rewards)}]")
    if rewards is not None:
        custom_reward_titles = ["Kill My Shell", "VIP"]
        for reward in list(filter(lambda x: x["title"] in custom_reward_titles, rewards)):
            await http_client.delete_custom_reward(broadcaster_id=broadcaster.id,
                                                   reward_id=reward["id"],
                                                   token=settings.USER_TOKEN)
            print(f"Deleted reward: [id={reward['id']}][title={reward['title']}]")


async def shoutout(channel: any, color: str):
    """ Post a shoutout announcement to chat; color = blue, green, orange, purple, or primary """
    await http_client.post_chat_announcement(token=settings.USER_TOKEN,
                                             broadcaster_id=broadcaster.id,
                                             message=f"Please check out {channel['broadcaster_name']}\'s channel https://www.twitch.tv/{channel['broadcaster_login']}! "
                                                     f"They were last playing \'{channel['game_name']}\'.",
                                             moderator_id=broadcaster.id,  # This ID must match the user ID in the user access token.
                                             color=color)  # blue green orange purple primary
    """ Perform a Twitch Shoutout command (https://help.twitch.tv/s/article/shoutouts?language=en_US). 
        The channel giving a Shoutout must be live. """
    streams = await http_client.get_streams(user_ids=[broadcaster.id])
    if len(streams) >= 1 and streams[0].type == 'live':
        await broadcaster.shoutout(token=settings.USER_TOKEN,
                                   to_broadcaster_id=channel['broadcaster_id'],
                                   moderator_id=broadcaster.id)


# TODO: add some discord commands https://discordpy.readthedocs.io/en/stable/


bot.run()
