from twitchio.ext import commands
from twitchio.ext import pubsub

import settings
from twitch import Twitch


class VIPCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.pubsub = pubsub.PubSubPool(bot)

        @bot.event()
        async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
            if event.reward.title == "VIP":  # title=VIP
                print('VIPCog pubsub_channel_points: ', event.id, event.reward, event.status, event.user, event.timestamp)
                await self.add_vip(event=event)

    async def add_vip(self, event: pubsub.PubSubChannelPointsMessage):
        mods = await Twitch(settings.BROADCASTER_ID).get_moderators(broadcaster_id=settings.BROADCASTER_ID)
        vips = await Twitch(settings.BROADCASTER_ID).get_vips(broadcaster_id=settings.BROADCASTER_ID)
        mods_user_ids = [user['user_id'] for user in mods]
        vips_user_ids = [user['user_id'] for user in vips]
        if event.user.id in mods_user_ids:
            print('user is a MOD')
        elif event.user.id in vips_user_ids:
            print('user already a VIP')
        else:
            await Twitch(settings.BROADCASTER_ID).add_channel_vip(event, settings.BROADCASTER_ID)


def prepare(bot: commands.Bot):
    bot.add_cog(VIPCog(bot))
