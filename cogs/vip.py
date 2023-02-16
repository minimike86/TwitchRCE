import twitchio
from twitchio import PartialUser, Chatter
from twitchio.ext import commands, pubsub
from twitchio.http import TwitchHTTP

import settings


class VIPCog(commands.Cog):

    def __init__(self, bot: commands.Cog):
        self.bot = bot

    @commands.Cog.event()
    async def event_message(self, message: twitchio.Message):
        if message.echo:
            return
        # print('VIPCog: ', message.author.name, message.content)

    @commands.command()
    async def add_channel_vip(self, event: commands.Context):
        pass

        # Authenticate the TwitchHTTP client a dumb way
        http_client: TwitchHTTP = self.bot._http
        http_client.client_id = settings.CLIENT_ID
        http_client.token = settings.USER_TOKEN

        mods = await http_client.get_channel_moderators(token=settings.USER_TOKEN, broadcaster_id=self.bot.user_id)
        mods_user_ids = [mod['user_id'] for mod in mods]

        vips = await http_client.get_channel_vips(token=settings.USER_TOKEN,
                                                  broadcaster_id=self.bot.user_id)
        vips_user_ids = [vip['user_id'] for vip in vips]

        if event.author.id in mods_user_ids:
            print(f'{event.author.display_name} is already a MOD')
            # TODO: add reward redemption.
            # await http_client.update_reward_redemption_status(token=settings.CHAT_OAUTH_ACCESS_TOKEN,
            #                                                   broadcaster_id=self.bot.user_id,
            #                                                   reward_id=event.id,
            #                                                   custom_reward_id=event.reward.id,
            #                                                   status=False)

        elif event.author.id in vips_user_ids:
            print(f'{event.author.display_name} is already a VIP')
            # TODO: add reward redemption.
            # await http_client.update_reward_redemption_status(token=settings.CHAT_OAUTH_ACCESS_TOKEN,
            #                                                   broadcaster_id=self.bot.user_id,
            #                                                   reward_id=event.id,
            #                                                   custom_reward_id=event.reward.id,
            #                                                   status=False)

        else:
            # TODO: twitchio.errors.Unauthorized: You're not authorized to use this route.
            await http_client.post_channel_vip(token=settings.CHAT_OAUTH_ACCESS_TOKEN,
                                               broadcaster_id=self.bot.user_id,
                                               user_id=event.author.id)

            # TODO: add reward redemption.
            # await http_client.update_reward_redemption_status(token=settings.CHAT_OAUTH_ACCESS_TOKEN,
            #                                                   broadcaster_id=self.bot.user_id,
            #                                                   reward_id=event.id,
            #                                                   custom_reward_id=event.reward.id,
            #                                                   status=True)
