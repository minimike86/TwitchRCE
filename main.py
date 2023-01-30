#!/usr/bin/env python3
import asyncio
import os

import twitchio
from twitchio import Channel
from twitchio.ext import eventsub, commands
import settings
from twitch import Twitch

esbot = commands.Bot.from_client_credentials(client_id=settings.TWITCH_CLIENT_ID,
                                             client_secret=settings.TWITCH_CLIENT_SECRET)
esclient = eventsub.EventSubClient(client=esbot,
                                   webhook_secret=settings.TWITCH_CLIENT_SECRET,
                                   callback_route="https://4a16-92-25-19-233.eu.ngrok.io/eventsub")


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(token=settings.TWITCH_CHAT_OAUTH, prefix='!', initial_channels=['msec'])

        # Constants
        self.loop = asyncio.get_event_loop()
        self.character_limit = 500
        self.channel: Channel | None = None

        # Load cogs
        for file in sorted(os.listdir("cogs")):
            if file.endswith(".py"):
                self.load_module("cogs." + file[:-3])

    async def __ainit__(self) -> None:
        self.loop.create_task(esclient.listen(port=8080))

        try:
            await esclient.subscribe_channel_follows(broadcaster=settings.BROADCASTER_ID)

            await esclient.subscribe_channel_cheers(broadcaster=settings.BROADCASTER_ID)

            await esclient.subscribe_channel_subscriptions(broadcaster=settings.BROADCASTER_ID)
            await esclient.subscribe_channel_subscription_end(broadcaster=settings.BROADCASTER_ID)
            await esclient.subscribe_channel_subscription_gifts(broadcaster=settings.BROADCASTER_ID)
            await esclient.subscribe_channel_subscription_messages(broadcaster=settings.BROADCASTER_ID)

            await esclient.subscribe_channel_raid(to_broadcaster=settings.BROADCASTER_ID)

            await esclient.subscribe_channel_bans(broadcaster=settings.BROADCASTER_ID)
            await esclient.subscribe_channel_unbans(broadcaster=settings.BROADCASTER_ID)

            await esclient.subscribe_channel_hypetrain_begin(broadcaster=settings.BROADCASTER_ID)
            await esclient.subscribe_channel_hypetrain_progress(broadcaster=settings.BROADCASTER_ID)
            await esclient.subscribe_channel_hypetrain_end(broadcaster=settings.BROADCASTER_ID)

            await esclient.subscribe_channel_poll_begin(broadcaster=settings.BROADCASTER_ID)
            await esclient.subscribe_channel_poll_progress(broadcaster=settings.BROADCASTER_ID)
            await esclient.subscribe_channel_poll_end(broadcaster=settings.BROADCASTER_ID)

            await esclient.subscribe_channel_prediction_begin(broadcaster=settings.BROADCASTER_ID)
            await esclient.subscribe_channel_prediction_progress(broadcaster=settings.BROADCASTER_ID)
            await esclient.subscribe_channel_prediction_lock(broadcaster=settings.BROADCASTER_ID)
            await esclient.subscribe_channel_prediction_end(broadcaster=settings.BROADCASTER_ID)

            await esclient.subscribe_channel_goal_begin(broadcaster=settings.BROADCASTER_ID)
            await esclient.subscribe_channel_goal_progress(broadcaster=settings.BROADCASTER_ID)
            await esclient.subscribe_channel_goal_end(broadcaster=settings.BROADCASTER_ID)

            await esclient.subscribe_channel_stream_start(broadcaster=settings.BROADCASTER_ID)
            await esclient.subscribe_channel_stream_end(broadcaster=settings.BROADCASTER_ID)

        except twitchio.HTTPException:
            pass

    async def event_ready(self):
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')

    async def event_message(self, message):
        # Messages with echo set to True are messages sent by the bot...
        # For now we just want to ignore them...
        if message.echo:
            return
        print('Bot: ', message.content)  # Print the contents of our message to console...

        # Since we have commands and are overriding the default `event_message`
        # We must let the bot know we want to handle and invoke our commands...
        await self.handle_commands(message)


bot = Bot()
bot.loop.run_until_complete(bot.__ainit__())
if bot.channel is None:
    bot.channel = bot.get_channel(settings.CHANNEL_NAME)


@esbot.command()
async def hello(self, ctx: commands.Context):
    await ctx.send(f'Hello {ctx.author.name}!')


@esbot.event()
async def event_eventsub_notification_stream_start(payload: eventsub.StreamOnlineData) -> None:
    print('Received StreamOnlineData event!')
    custom_reward_ids = await Twitch(settings.BROADCASTER_ID).get_custom_rewards()
    if custom_reward_ids is not None:
        for reward in list(filter(lambda x: x["title"] == "Kill My Shell" or x["title"] == "VIP", custom_reward_ids)):
            await Twitch(settings.BROADCASTER_ID).delete_custom_reward(reward["id"])
    await Twitch(settings.BROADCASTER_ID).create_custom_reward("Kill My Shell", 6666, True, 5 * 60)
    await Twitch(settings.BROADCASTER_ID).create_custom_reward("VIP", 20000)
    if bot.channel is None:
        bot.channel = bot.get_channel(settings.CHANNEL_NAME)
    await bot.channel.send(f'This stream is now online!')


@esbot.event()
async def event_eventsub_notification_stream_end(payload: eventsub.StreamOfflineData) -> None:
    print('Received StreamOfflineData event!')
    custom_reward_ids = await Twitch(settings.BROADCASTER_ID).get_custom_rewards()
    if custom_reward_ids is not None:
        for reward in list(
                filter(lambda x: x["title"] == "Kill My Shell" or x["title"] == "VIP", custom_reward_ids)):
            await Twitch(settings.BROADCASTER_ID).delete_custom_reward(reward["id"])
    if bot.channel is None:
        bot.channel = bot.get_channel(settings.CHANNEL_NAME)
    await bot.channel.send(f'This stream is now offline!')
    exit(0)


@esbot.event()
async def event_eventsub_notification_follow(payload: eventsub.ChannelFollowData) -> None:
    print('Received ChannelFollowData event!')
    if bot.channel is None:
        bot.channel = bot.get_channel(settings.CHANNEL_NAME)
    await bot.channel.send(f'{payload.data.user.name} followed woohoo! {payload.data.followed_at}!')


@esbot.event()
async def event_eventsub_notification_subscription(payload: eventsub.ChannelSubscribeData) -> None:
    print('Received ChannelSubscribeData event!')
    if bot.channel is None:
        bot.channel = bot.get_channel(settings.CHANNEL_NAME)
    await bot.channel.send(f'{payload.data.user.name} subscribed with {payload.data.tier} {payload.data.is_gift}! ')


@esbot.event()
async def event_eventsub_notification_raid(payload: eventsub.ChannelRaidData) -> None:
    print('Received ChannelRaidData event!')
    if bot.channel is None:
        bot.channel = bot.get_channel(settings.CHANNEL_NAME)
    await bot.channel.send(f'{payload.data.raider.name} raided the channel with {payload.data.viewer_count} viewers! ')


bot.run()
