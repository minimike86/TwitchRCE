#!/usr/bin/env python3
from twitchio.ext import pubsub, eventsub
from twitch import Twitch
from bot import Bot
import settings


async def main():
    topics = [
        pubsub.channel_subscriptions(settings.ACCESS_TOKEN)[settings.BROADCASTER_ID],
        pubsub.channel_points(settings.ACCESS_TOKEN)[settings.BROADCASTER_ID],
        pubsub.bits(settings.ACCESS_TOKEN)[settings.BROADCASTER_ID]
    ]
    await bot.pubsub.subscribe_topics(topics)

    # eventsub_client = eventsub.EventSubClient(bot,
    #                                           webhook_secret=settings.TWITCH_CLIENT_SECRET,
    #                                           callback_route="/callback")
    # bot.loop.create_task(eventsub_client.listen(port=4000))
    # await eventsub_client.subscribe_channel_raid(from_broadcaster=settings.BROADCASTER_ID)

    await bot.start()


async def setup():
    custom_reward_id = await Twitch(settings.BROADCASTER_ID).get_custom_reward()
    if custom_reward_id is not None:
        await Twitch(settings.BROADCASTER_ID).delete_custom_reward(custom_reward_id)
    await Twitch(settings.BROADCASTER_ID).create_custom_reward("Kill My Shell", 666, True, 5 * 60)


if __name__ == "__main__":
    bot = Bot()
    bot.pubsub = pubsub.PubSubPool(bot)
    bot.loop.run_until_complete(setup())

    @bot.event()
    async def event_pubsub_bits(event: pubsub.PubSubBitsMessage):
        print('pubsub_bits: ', event.bits_used, event.message, event.user)
        pass  # do stuff on bit redemptions

    @bot.event()
    async def event_pubsub_sub(event: pubsub.PubSubChannelSubscribe):
        print('pubsub_sub: ', event.sub_plan, event.sub_plan_name, event.cumulative_months, event.is_gift,
              event.recipient, event.streak_months, event.message, event.user)
        pass  # do stuff on subscription

    @bot.event()
    async def event_eventsub_raid(event: eventsub.ChannelRaidData):
        print('eventsub_sub: ', event.raider, event.reciever, event.viewer_count)
        pass

    bot.loop.run_until_complete(main())
