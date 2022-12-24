from twitchio.ext import commands
from twitchio.ext import pubsub


class VIPCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.pubsub = pubsub.PubSubPool(bot)

        @bot.event()
        async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
            if event.reward.title == "VIP":  # title=VIP
                print('VIPCog pubsub_channel_points: ', event.id, event.reward, event.status, event.user, event.timestamp)
                await self.add_vip(self, event)

    @staticmethod
    async def add_vip(self, event: pubsub.PubSubChannelPointsMessage):
        pass


def prepare(bot: commands.Bot):
    bot.add_cog(VIPCog(bot))