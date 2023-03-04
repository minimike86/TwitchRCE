import twitchio
from twitchio.ext import commands

import custombot


class VIPCog(commands.Cog):

    def __init__(self, bot: custombot.Bot):
        self.bot = bot

    @commands.Cog.event()
    async def event_message(self, message: twitchio.Message):
        if message.echo:
            return
        # print('VIPCog: ', message.author.name, message.content)

    @commands.command()
    async def add_channel_vip(self, ctx: commands.Context):
        broadcaster = await self.bot._http.get_users(ids=[], logins=[ctx.channel.name])
        row = self.bot.db.fetch_user_access_token_from_id(self.bot.user_id)

        # Get list of channel mods
        # mods = await self.bot._http.get_channel_moderators(token=row['access_token'],
        #                                                    broadcaster_id=str(broadcaster[0]['id']))
        # mods_user_ids = [mod['user_id'] for mod in mods]

        # Get list of channel vips
        # vips = await self.bot._http.get_channel_vips(token=row['access_token'],
        #                                              broadcaster_id=str(broadcaster[0]['id']))
        # vips_user_ids = [vip['user_id'] for vip in vips]

        if ctx.author.is_mod:
            """ Check if the redeemer is already a moderator and abort """
            print(f'{ctx.author.display_name} is already a MOD')
            # TODO: figure out correct type of event and pass correct object to update_reward_redemption_status()
            # await self.bot._http.update_reward_redemption_status(token=row['access_token'],
            #                                                      broadcaster_id=str(broadcaster[0]['id']),
            #                                                      reward_id=event.id,
            #                                                      custom_reward_id=event.reward.id,
            #                                                      status=False)
        elif ctx.author.is_vip:
            """ Check if the redeemer is already a VIP and abort """
            print(f'{ctx.author.display_name} is already a VIP')
            # TODO: figure out correct type of event and pass correct object to update_reward_redemption_status()
            # await self.bot._http.update_reward_redemption_status(token=row['access_token'],
            #                                                      broadcaster_id=str(broadcaster[0]['id']),
            #                                                      reward_id=event.id,
            #                                                      custom_reward_id=event.reward.id,
            #                                                      status=False)

        else:
            """ Add redeemer as a VIP, and auto-fulfill the redemption """
            await self.bot._http.post_channel_vip(token=row['access_token'],
                                                  broadcaster_id=str(broadcaster[0]['id']),
                                                  user_id=ctx.author.id)
            # TODO: figure out correct type of event and pass correct object to update_reward_redemption_status()
            # await self.bot._http.update_reward_redemption_status(token=row['access_token'],
            #                                                      broadcaster_id=str(broadcaster[0]['id']),
            #                                                      reward_id=event.id,
            #                                                      custom_reward_id=event.reward.id,
            #                                                      status=True)
