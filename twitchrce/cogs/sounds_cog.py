import twitchio
from twitchio.ext import commands

# import soundfile as sf

from twitchrce import custom_bot


class SoundsCog(commands.Cog):

    def __init__(self, bot: custom_bot.Bot):
        self.bot = bot

    @commands.Cog.event()
    async def event_message(self, message: twitchio.Message):
        if message.echo:
            return
        print("SoundCog: ", message.author.name, message.content)

    # @commands.command()
    # async def youtube(self, ctx: commands.Context):
    #     param: str = str(ctx.message.content).split(maxsplit=1)[1]
    #     track = await sounds.Sound.ytdl_search(search=param)
    #     self.bot.yt_player.play(track)
    #     await ctx.send(f'Now playing: {track.title}')
    #
    # @commands.command()
    # async def later(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/a-few-moments-later-hd.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def ahfuck(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/ah-fuck.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def wow(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/anime-wow.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def bruh(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/bruh.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def dialup(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/dial_up.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def emodmg(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/emotional-damage-meme.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def buzzer(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/family-fortunes-wrong-buzzer.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def fbi(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/fbi-open-up-sfx.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def friend(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/friend.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def fthis(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/fuck-this-shit-im-out.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def gg(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/gg.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def goforit(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/go-for-it.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def hackerman(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/hackerman.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def hellomf(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/hello_motherfrucker.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def hexy(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/hexy-hacker.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def ignore(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/ignore.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def wierd(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/internets-wierd.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def sellwife(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/i-selled-my-wife.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def heknew(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/it-was-at-this-moment-that-he-he-knew.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def kerb(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/kerb-your-enthusiasm.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def gothim(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/ladies-and-gentlemen-we-got-him-song.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def leeroy(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/leroy-jenkins.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def lies(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/lies_on_the_internet.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def mgsalert(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/mgsalert.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def hellothere(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/obi-wan-hello-there.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def order66(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/order66.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def over9000(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/over9000.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def hackercrap(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/please-god-damn-it-i-hate-this-hacker-crap.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def sadviolin(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/sadviolin.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def satan(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/satan.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def stepbro(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/stepbro.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command(aliases=['surprize'])
    # async def surprise(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/surprise-motherfucker.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def tsdisconnect(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/teamspeak-disconnected.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def trollolol(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/trollolol.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def usbconnect(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/usbconnect.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def usbdisconnect(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/usbdisconnect.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def victory(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/victoryff7.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def shutdown(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/winxp-shutdown.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
    #
    # @commands.command()
    # async def wtfinternet(self, ctx: commands.Context):
    #     sound_file = '/home/kali/Music/wtf-is-the-internet.mp3'
    #     data, samplerate = sf.read(sound_file)
    #     self.bot.sd.play(data, samplerate)
