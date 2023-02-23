import twitchio
from twitchio.ext import commands
from twitchio.http import TwitchHTTP

import settings


class VIPCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.event()
    async def event_message(self, message: twitchio.Message):
        if message.echo:
            return
        # print('VIPCog: ', message.author.name, message.content)

    @commands.command()
    async def add_channel_vip(self, event: commands.Context):
        # TODO: figure out correct type of event and pass correct object to update_reward_redemption_status()

        # Get list of channel mods
        mods = await self.bot._http.get_channel_moderators(token=settings.USER_TOKEN,
                                                           broadcaster_id=self.bot.user_id)
        mods_user_ids = [mod['user_id'] for mod in mods]

        # Get list of channel vips
        vips = await self.bot._http.get_channel_vips(token=settings.USER_TOKEN,
                                                     broadcaster_id=self.bot.user_id)
        vips_user_ids = [vip['user_id'] for vip in vips]

        if event.author.id in mods_user_ids:
            """ Check if the redeemer is already a moderator and abort """
            print(f'{event.author.display_name} is already a MOD')
            await self.bot._http.update_reward_redemption_status(token=settings.USER_TOKEN,
                                                                 broadcaster_id=self.bot.user_id,
                                                                 reward_id=event.id,
                                                                 custom_reward_id=event.reward.id,
                                                                 status=False)
        elif event.author.id in vips_user_ids:
            """ Check if the redeemer is already a VIP and abort """
            print(f'{event.author.display_name} is already a VIP')
            await self.bot._http.update_reward_redemption_status(token=settings.USER_TOKEN,
                                                                 broadcaster_id=self.bot.user_id,
                                                                 reward_id=event.id,
                                                                 custom_reward_id=event.reward.id,
                                                                 status=False)

        else:
            """ Add redeemer as a VIP, and auto-fulfill the redemption """
            await self.bot._http.post_channel_vip(token=settings.USER_TOKEN,
                                                  broadcaster_id=self.bot.user_id,
                                                  user_id=event.author.id)
            await self.bot._http.update_reward_redemption_status(token=settings.USER_TOKEN,
                                                                 broadcaster_id=self.bot.user_id,
                                                                 reward_id=event.id,
                                                                 custom_reward_id=event.reward.id,
                                                                 status=True)
