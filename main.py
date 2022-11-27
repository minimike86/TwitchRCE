#!/usr/bin/env python3
from twitchio.ext import pubsub

from twitch import Twitch
from bot import Bot
import settings


async def main():
    topics = [
        pubsub.channel_points(settings.ACCESS_TOKEN)[settings.BROADCASTER_ID],
        pubsub.bits(settings.ACCESS_TOKEN)[settings.BROADCASTER_ID]
    ]
    await bot.pubsub.subscribe_topics(topics)
    await bot.start()


async def setup():
    custom_reward_id = await Twitch(settings.BROADCASTER_ID).get_custom_reward()
    await Twitch(settings.BROADCASTER_ID).delete_custom_reward(custom_reward_id)
    await Twitch(settings.BROADCASTER_ID).create_custom_reward("Kill My Shell", 10000, True, 5 * 60)


if __name__ == "__main__":
    bot = Bot()
    bot.pubsub = pubsub.PubSubPool(bot)

    bot.loop.run_until_complete(setup())

    @bot.event()
    async def event_pubsub_bits(event: pubsub.PubSubBitsMessage):
        print('pubsub_bits: ', event.bits_used, event.message, event.user)
        pass  # do stuff on bit redemptions

    bot.loop.run_until_complete(main())
