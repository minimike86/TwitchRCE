import twitchio
from twitchio import PartialUser
from twitchio.ext import commands

import custom_bot


# TODO: add sound extensions commands https://twitchio.dev/en/latest/exts/sounds.html
class UserCog(commands.Cog):

    def __init__(self, bot: custom_bot.Bot):
        self.bot = bot

    @commands.Cog.event()
    async def event_message(self, message: twitchio.Message):
        if message.echo:
            return
        # print('RCECog: ', message.author.name, message.content)

    @commands.command(aliases=['ohlook'])
    async def stairsthetrashman(self, ctx: commands.Context):
        """ type !stairsthetrashman or !ohlook """
        if ctx.author.display_name.lower() in ['stairsthetrashman', 'msec']:
            await ctx.send(f'Oh look, it\'s the bitch!')
            to_shoutout_user = await self.bot._http.get_users(ids=[], logins=['stairsthetrashman'])
            to_shoutout_channel = await self.bot._http.get_channels(broadcaster_id=to_shoutout_user[0]['id'])
            from_broadcaster: PartialUser = list(filter(lambda x: x.name == ctx.channel.name, self.bot.channel_broadcasters))[0]
            await self.bot.announce_shoutout(broadcaster=from_broadcaster, channel=to_shoutout_channel[0], color='blue')

    @commands.command(aliases=['lottie'])
    async def lottiekins(self, ctx: commands.Context):
        """ type !lottiekins or !lottie """
        if ctx.author.display_name.lower() in ['lottiekins', 'msec']:
            lottiekins = list(filter(lambda x: x.name == 'lottiekins', self.bot.channel_broadcasters))[0]
            await lottiekins.send('hi my name is lottie im a stupid do do head')
