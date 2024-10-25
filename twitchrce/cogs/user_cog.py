import twitchio
from twitchio.ext import commands

from twitchrce import custom_bot

# import soundfile as sf


class UserCog(commands.Cog):

    def __init__(self, bot: custom_bot.Bot):
        self.bot = bot

    @commands.Cog.event()
    async def event_message(self, message: twitchio.Message):
        if message.echo:
            return
        print("UserCog: ", message.author.name, message.content)

    @commands.command(aliases=["stairs1", "ohlook"])
    async def stairsthetrashman1(self, ctx: commands.Context):
        """type !stairsthetrashman or !ohlook"""
        if ctx.author.display_name.lower() in ["stairsthetrashman", "msec"]:
            sound_file = "/home/kali/Music/ohlook.mp3"
            # data, samplerate = sf.read(sound_file)
            # self.bot.sd.play(data, samplerate)

    @commands.command(aliases=["stairs2", "because"])
    async def stairsthetrashman2(self, ctx: commands.Context):
        if ctx.author.display_name.lower() in ["stairsthetrashman", "msec"]:
            sound_file = "/home/kali/Music/Because_Im_mexican.mp3"
            # data, samplerate = sf.read(sound_file)
            # self.bot.sd.play(data, samplerate)

    @commands.command(aliases=["stairs3", "sonofagun"])
    async def stairsthetrashman3(self, ctx: commands.Context):
        if ctx.author.display_name.lower() in ["stairsthetrashman", "msec"]:
            sound_file = "/home/kali/Music/yousonofagun.mp3"
            # data, samplerate = sf.read(sound_file)
            # self.bot.sd.play(data, samplerate)

    @commands.command(aliases=["alh4zr3d", "alhashes"])
    async def alh4zr3d1(self, ctx: commands.Context):
        if ctx.author.display_name.lower() in ["alh4zr3d", "msec"]:
            sound_file = "/home/kali/Music/al-fully-erect.mp3"
            # data, samplerate = sf.read(sound_file)
            # self.bot.sd.play(data, samplerate)

    @commands.command(aliases=["tibs", "0xtib3rius", "sofgood"])
    async def tibs1(self, ctx: commands.Context):
        if ctx.author.display_name.lower() in ["0xtib3rius", "msec"]:
            sound_file = "/home/kali/Music/tibs1_sofgood.mp3"
            # data, samplerate = sf.read(sound_file)
            # self.bot.sd.play(data, samplerate)

    @commands.command(aliases=["trshpuppy", "sbacunt"])
    async def trshpuppy1(self, ctx: commands.Context):
        if ctx.author.display_name.lower() in ["trshpuppy", "msec"]:
            sound_file = "/home/kali/Music/trashpuppy_stop-being-a-cunt.mp3"
            # data, samplerate = sf.read(sound_file)
            # self.bot.sd.play(data, samplerate)

    @commands.command(aliases=["fcamerayo"])
    async def trshpuppy2(self, ctx: commands.Context):
        if ctx.author.display_name.lower() in ["trshpuppy", "msec"]:
            sound_file = "/home/kali/Music/trashpuppy_fucking-camera-yo.mp3"
            # data, samplerate = sf.read(sound_file)
            # self.bot.sd.play(data, samplerate)
