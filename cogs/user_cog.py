import twitchio
from twitchio import PartialUser
from twitchio.ext import commands, sounds

import custom_bot


class UserCog(commands.Cog):

    def __init__(self, bot: custom_bot.Bot):
        self.bot = bot

    @commands.Cog.event()
    async def event_message(self, message: twitchio.Message):
        if message.echo:
            return
        # print('RCECog: ', message.author.name, message.content)

    @commands.command(aliases=['ohlook'])
    async def stairsthetrashman1(self, ctx: commands.Context):
        """ type !stairsthetrashman or !ohlook """
        if ctx.author.display_name.lower() in ['stairsthetrashman', 'msec']:
            await ctx.send(f'Oh look, it\'s the bitch!')
            to_shoutout_user = await self.bot._http.get_users(ids=[], logins=['stairsthetrashman'])
            to_shoutout_channel = await self.bot._http.get_channels(broadcaster_id=to_shoutout_user[0]['id'])
            from_broadcaster: PartialUser = list(filter(lambda x: x.name == ctx.channel.name, self.bot.channel_broadcasters))[0]
            await self.bot.announce_shoutout(ctx=None, broadcaster=from_broadcaster, channel=to_shoutout_channel[0], color='blue')
            sound = sounds.Sound(source='/home/kali/Music/ohlook.mp3')
            self.bot.player.play(sound)

    @commands.command(aliases=['because'])
    async def stairsthetrashman2(self, ctx: commands.Context):
        if ctx.author.display_name.lower() in ['stairsthetrashman', 'msec']:
            sound = sounds.Sound(source='/home/kali/Music/Because_Im_mexican.mp3')
            self.bot.player.play(sound)

    @commands.command(aliases=['sonofagun'])
    async def stairsthetrashman3(self, ctx: commands.Context):
        if ctx.author.display_name.lower() in ['stairsthetrashman', 'msec']:
            sound = sounds.Sound(source='/home/kali/Music/yousonofagun.mp3')
            self.bot.player.play(sound)

    @commands.command(aliases=['lottie'])
    async def lottiekins(self, ctx: commands.Context):
        """ type !lottiekins or !lottie """
        if ctx.author.display_name.lower() in ['lottiekins', 'msec']:
            lottiekins = list(filter(lambda x: x.name == 'lottiekins', self.bot.channel_broadcasters))[0]
            await lottiekins.send('hi my name is lottie im a stupid do do head')
