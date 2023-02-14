import twitchio
from twitchio.ext import commands, pubsub


class VIPCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.event()
    async def event_message(self, message: twitchio.Message):
        if message.echo:
            return
        # print('VIPCog: ', message.author.name, message.content)

    @commands.command()
    async def add_channel_vip(self, event: pubsub.PubSubChannelPointsMessage):
        pass

        # TODO: twitchio.errors.Unauthorized: You're not authorized to use this route.
        # mods = await self.bot._http.get_channel_moderators(token=settings.CHAT_OAUTH_ACCESS_TOKEN,
        #                                                    broadcaster_id=self.bot.user_id)
        # mods_user_ids = [user['user_id'] for user in mods]
        # TODO: twitchio.errors.Unauthorized: You're not authorized to use this route.
        # vips = await self.bot._http.get_channel_vips(token=settings.CHAT_OAUTH_ACCESS_TOKEN,
        #                                              broadcaster_id=self.bot.user_id)
        # vips_user_ids = [user['user_id'] for user in vips]
        # if event.user.id in mods_user_ids:
        #     print('user is already a MOD')
        #     # TODO: twitchio.errors.Unauthorized: You're not authorized to use this route.
        #     await self.bot._http.update_reward_redemption_status(token=settings.CHAT_OAUTH_ACCESS_TOKEN,
        #                                                          broadcaster_id=self.bot.user_id,
        #                                                          reward_id=event.id,
        #                                                          custom_reward_id=event.reward.id,
        #                                                          status=False)

        # elif event.user.id in vips_user_ids:
        #     print('user is already a VIP')
        #     # TODO: twitchio.errors.Unauthorized: You're not authorized to use this route.
        #     await self.bot._http.update_reward_redemption_status(token=settings.CHAT_OAUTH_ACCESS_TOKEN,
        #                                                          broadcaster_id=self.bot.user_id,
        #                                                          reward_id=event.id,
        #                                                          custom_reward_id=event.reward.id,
        #                                                          status=False)

        # else:
        #     # TODO: twitchio.errors.Unauthorized: You're not authorized to use this route.
        #     await self.bot._http.post_channel_vip(token=settings.CHAT_OAUTH_ACCESS_TOKEN,
        #                                           broadcaster_id=self.bot.user_id,
        #                                           user_id=event.user.id)
        #
        #     # TODO: twitchio.errors.Unauthorized: You're not authorized to use this route.
        #     await self.bot._http.update_reward_redemption_status(token=settings.CHAT_OAUTH_ACCESS_TOKEN,
        #                                                          broadcaster_id=self.bot.user_id,
        #                                                          reward_id=event.id,
        #                                                          custom_reward_id=event.reward.id,
        #                                                          status=True)
