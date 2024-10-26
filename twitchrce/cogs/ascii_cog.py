import twitchio
from twitchio.ext import commands

from twitchrce import custom_bot


class AsciiCog(commands.Cog):

    def __init__(self, bot: custom_bot.CustomBot):
        self.bot = bot

    @commands.Cog.event()
    async def event_message(self, message: twitchio.Message):
        if message.echo:
            return
        # print('RCECog: ', message.author.name, message.content)

    @commands.command()
    async def kill_everyone(self, ctx: commands.Context):
        """invoke skynet"""
        await ctx.send(f"Killing everyone... starting with {ctx.author.name}!")

    @commands.command()
    async def mario(self, ctx: commands.Context):
        await ctx.send(
            f"⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛⬛ "
            f"⬛⬛⬛⬛⬛🟥🟥🟥🟥🟥⬛⬛⬛⬛⬛⬛ "
            f"⬛⬛⬛⬛🟥🟥🟥🟥🟥🟥🟥🟥🟥⬛⬛⬛ "
            f"⬛⬛⬛⬛🟫🟫🟫🟨🟨⬛🟨⬛⬛⬛⬛⬛ "
            f"⬛⬛⬛🟫🟨🟫🟨🟨🟨⬛🟨🟨🟨⬛⬛⬛ "
            f"⬛⬛⬛🟫🟨🟫🟫🟨🟨🟨🟫🟨🟨🟨⬛⬛ "
            f"⬛⬛⬛🟫🟫🟨🟨🟨🟨🟫🟫🟫🟫⬛⬛⬛ "
            f"⬛⬛⬛⬛⬛🟨🟨🟨🟨🟨🟨🟨⬛⬛⬛⬛ "
            f"⬛⬛⬛⬛🟥🟥🟦🟥🟥🟦🟥⬛⬛⬛⬛⬛ "
            f"⬛⬛⬛🟥🟥🟥🟦🟥🟥🟦🟥🟥🟥⬛⬛⬛ "
            f"⬛⬛🟥🟥🟥🟥🟦🟦🟦🟦🟥🟥🟥🟥⬛⬛ "
            f"⬛⬛⬜⬜🟥🟦🟨🟦🟦🟨🟦🟥⬜⬜⬛⬛ "
            f"⬛⬛⬜⬜⬜🟦🟦🟦🟦🟦🟦⬜⬜⬜⬛⬛ "
            f"⬛⬛⬜⬜🟦🟦🟦⬛⬛🟦🟦🟦⬜⬜⬛⬛ "
            f"⬛⬛⬛⬛🟦🟦🟦⬛⬛🟦🟦🟦⬛⬛⬛⬛ "
            f"⬛⬛⬛🟫🟫🟫⬛⬛⬛⬛🟫🟫🟫⬛⬛⬛ "
            f"⬛⬛🟫🟫🟫🟫⬛⬛⬛⬛🟫🟫🟫🟫⬛⬛"
        )

    @commands.command()
    async def spider(self, ctx: commands.Context):
        await ctx.send(
            f"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ " f"╱╲⎝⧹༼◕ ͜ﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞo.◕ ༽⧸⎠╱╲"
        )

    @commands.command()
    async def spiderswarm(self, ctx: commands.Context):
        await ctx.send(
            f"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ "
            f"╱╲⎝⧹༼◕ ͜ﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞo.◕ ༽⧸⎠╱╲"
            f"⠀╱╲⎝⧹༼◕ ͜ﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞo.◕ ༽⧸⎠╱╲"
            f"╱╲⎝⧹༼◕ ͜ﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞo.◕ ༽⧸⎠╱╲⠀⠀"
            f"╱╲⎝⧹༼◕ ͜ﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞo.◕ ༽⧸⎠╱╲⠀⠀⠀"
            f"╱╲⎝⧹༼◕ ͜ﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞo.◕ ༽⧸⎠╱╲⠀⠀⠀⠀"
            f"╱╲⎝⧹༼◕ ͜ﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞo.◕ ༽⧸⎠╱╲⠀⠀⠀⠀⠀"
            f"╱╲⎝⧹༼◕ ͜ﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞﱞo.◕ ༽⧸⎠╱╲⠀⠀⠀⠀⠀⠀"
        )

    @commands.command()
    async def deez(self, ctx: commands.Context):
        await ctx.send(
            f" ⠀⠀⠀⣤⣤⣤⣤⣀⠀⠀⣤⣤⣤⣤⡄⠀⣤⣤⣤⣤⠀⣤⣤⣤⣤⣤⠀⠀⠀⠀"
            f" ⠀⠀⠀⣿⡇⠀⠈⢻⣧⠀⣿⡇⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⢠⡾⠃⠀⠀⠀⠀"
            f" ⠀⠀⠀⣿⡇⠀⠀⢸⣿⠀⣿⡟⠛⠛⠀⠀⣿⠛⠛⠓⠀⠀⣠⡿⠁⠀⠀⠀⠀⠀"
            f" ⠀⠀⠀⣿⡇⢀⣀⣾⠏⠀⣿⡇⠀⠀⠀⠀⣿⠀⠀⠀⠀⣴⡟⠁⠀⠀⠀⠀⠀⠀"
            f" ⠀⠀⠀⠛⠛⠛⠋⠁⠀⠀⠛⠛⠛⠛⠃⠀⠛⠛⠛⠛⠁⠛⠛⠛⠛⠛⠀ ⠀⠀"
            f"⠀⠀⠀⣿⣿⡄⠀⢸⣿⠀⢸⡇⠀⠀⠀⣿⠀⠛⠛⢻⡟⠛⠋⣴⡟⠋⠛⠃ ⠀⠀"
            f"⠀⠀⠀⣿⠘⣿⡄⢸⣿⠀⢸⡇⠀⠀⠀⣿⠀⠀⠀⢸⡇⠀⠀⠙⢿⣦⣄⠀ ⠀⠀"
            f"⠀⠀⠀⣿⠀⠈⢿⣾⣿⠀⢸⣇⠀⠀⠀⣿⠀⠀⠀⢸⡇⠀⠀⠀⠀⠈⢻⣷ ⠀⠀"
            f"⠀⠀⠀⠿⠀⠀⠈⠿⠿⠀⠈⠻⠶⠶⠾⠋⠀⠀⠀⠸⠇⠀⠀⠻⠶⠶⠿⠃"
        )

    @commands.command()
    async def secplus(self, ctx: commands.Context):
        await ctx.send(
            f"⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄"
            f"⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄"
            f"⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄"
            f"⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄"
            f"⢀⡤⠤⠤⣄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠠⠤⢤⡤⠤⠄⣄⠄⢀⡤⡄⠄⠄"
            f"⣾⠄⠄⠄⠈⢡⠖⠛⢲⣰⡞⢳⡞⢳⡆⡴⠚⠳⣆⢸⡇⠄⠄⣿⠄⣼⣁⣳⡄⠄"
            f"⠘⠦⠤⠤⠖⠘⠦⠤⠼⠹⠇⠸⠇⠸⠇⡇⠤⠴⠏⠘⠇⠄⠄⠿⠸⠋⠉⠉⠳⠄"
            f"⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠃⠄⠄⣀⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄"
            f"⠄⠄⠰⣏⣙⠃⣠⠤⣄⢠⡤⣄⢠⡄⢠⡄⣤⡄⣭⠠⣿⢤⣄⣠⣄⣰⣆⡀⠄⠄"
            f"⠄⠄⠰⣮⣹⡇⢻⣟⡟⠸⣇⡤⠸⣇⣼⡇⣿⠄⣿⠄⣿⡀⢻⡟⠈⠹⠏⠁⠄⠄"
            f"⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠚⠁⠄⠄⠄⠄⠄⠄"
            f"⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄"
            f"⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄"
            f"⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄"
            f"⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄"
        )

    @commands.command()
    async def letsgo(self, ctx: commands.Context):
        await ctx.send(
            f"⣤⣶⣶⣶⣶⡆⢀⣴⣶⣿⣿⣿⣶⣤⡀⠀⣸⣿⣿⣿⣿⡇⠀⢠⣶⣾⣿⣶⣶⡄ "
            f"⢸⣿⣿⣿⣿⡇⣾⣿⡟⠉⣉⣿⣿⣿⠷⠀⣿⣿⣿⣿⣿⠁⠀⠹⠿⢿⣿⣿⣿⣿ "
            f"⢸⣿⣿⣿⣿⡇⣿⣿⣷⣿⣿⠟⠋⠀⢰⣶⣿⣿⣿⣿⣿⣿⣿⡇⠀⢀⣼⣿⡿⠁ "
            f"⢸⣿⣿⣿⣿⡇⢻⣿⣿⣿⣶⣶⣾⡇⢸⣿⣿⣿⣿⣿⣿⠟⠛⠓⠀⠉⠛⠁⠀⠀ "
            f"⠀⣿⣿⣿⣿⣷⠀⠙⠻⠿⠿⠟⠛⠁⠈⠉⣿⣿⣿⣿⡇⠀⣠⣾⣿⣿⣿⣷⣦⠀ "
            f"⠀⣿⣿⣿⣿⣿⣧⣤⣀⣀⣤⣤⣴⣶⣿⠀⣿⣿⣿⣿⡇⠀⣿⣿⣿⣿⠉⠉⠋⠀ "
            f"⠀⠘⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠸⣿⣿⣿⣿⣄⠙⢿⣿⣿⣿⣦⡀⠀ "
            f"⠀⠀⠀⠉⠛⠛⠛⠛⠛⠛⠛⢉⣉⣁⣀⣤⠀⠙⠻⣿⣿⣿⣿⠀⠙⣿⣿⣿⣿⡀ "
            f"⠀⠀⢀⣴⣾⣿⣿⣿⣿⣿⣷⣾⣿⣿⣿⣿⠀⢸⣶⣤⣀⣉⣉⣀⣠⣿⣿⣿⣿⡇ "
            f"⠀⢠⣿⣿⣿⣿⣿⠟⠛⠛⠛⢿⣿⣿⣿⣿⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠀ "
            f"⠀⢸⣿⣿⣿⣿⣿⣄⣀⣀⣀⣼⣿⣿⣿⣿⠀⠈⠉⠙⠛⠛⠛⠛⠛⠛⠛⠉⠀⠀ "
            f"⠀⠈⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⣠⣶⣿⣿⣿⣿⣿⣶⣤⡀⠀⠀⠀ "
            f"⠀⠀⠀⠘⠻⠿⣿⣿⣿⠿⠛⣿⣿⣿⣿⡿⢰⣿⣿⣿⡿⠛⠿⣿⣿⣿⣿⡄⠀⠀ "
            f"⠀⠀⢀⣾⣶⣄⡀⠀⠀⢀⣴⣿⣿⣿⣿⡇⢸⣿⣿⣿⣄⣀⣠⣿⣿⣿⣿⡗⠀⠀ "
            f"⠀⠀⢾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⢿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠃⠀⠀ "
            f"⠀⠀⠀⠈⠛⠻⠿⣿⣿⣿⣿⡿⠿⠛⠁⠀⠀⠀⠙⠻⠿⣿⣿⠿⠟⠋"
        )

    @commands.command()
    async def capybara(self, ctx: commands.Context):
        await ctx.send(
            f"⠀⠀⢀⣀⠤⠿⢤⢖⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ "
            f"⡔⢩⠂⠀⠒⠗⠈⠀⠉⠢⠄⣀⠠⠤⠄⠒⢖⡒⢒⠂⠤⢄⠀⠀⠀⠀ "
            f"⠇⠤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠈⠀⠈⠈⡨⢀⠡⡪⠢⡀⠀ "
            f"⠈⠒⠀⠤⠤⣄⡆⡂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠢⠀⢕⠱⠀ "
            f"⠀⠀⠀⠀⠀⠈⢳⣐⡐⠐⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠁⠇ "
            f"⠀⠀⠀⠀⠀⠀⠀⠑⢤⢁⠀⠆⠀⠀⠀⠀⠀⢀⢰⠀⠀⠀⡀⢄⡜⠀ "
            f"⠀⠀⠀⠀⠀⠀⠀⠀⠘⡦⠄⡷⠢⠤⠤⠤⠤⢬⢈⡇⢠⣈⣰⠎⠀⠀ "
            f"⠀⠀⠀⠀⠀⠀⠀⠀⠀⣃⢸⡇⠀⠀⠀⠀⠀⠈⢪⢀⣺⡅⢈⠆⠀⠀ "
            f"⠀⠀⠀⠀⠀⠀⠀⠶⡿⠤⠚⠁⠀⠀⠀⢀⣠⡤⢺⣥⠟⢡⠃⠀⠀⠀ "
            f"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠀⠀⠀⠀⠀⠀ Capybara says go play"
        )

    @commands.command()
    async def weeb1(self, ctx: commands.Context):
        await ctx.send(
            f"⣿⣿⣷⡁⢆⠈⠕⢕⢂⢕⢂⢕⢂⢔⢂⢕⢄⠂⣂⠂⠆⢂⢕⢂⢕⢂⢕⢂⢕⢂ "
            f"⣿⣿⣿⡷⠊⡢⡹⣦⡑⢂⢕⢂⢕⢂⢕⢂⠕⠔⠌⠝⠛⠶⠶⢶⣦⣄⢂⢕⢂⢕ "
            f"⣿⣿⠏⣠⣾⣦⡐⢌⢿⣷⣦⣅⡑⠕⠡⠐⢿⠿⣛⠟⠛⠛⠛⠛⠡⢷⡈⢂⢕⢂ "
            f"⠟⣡⣾⣿⣿⣿⣿⣦⣑⠝⢿⣿⣿⣿⣿⣿⡵⢁⣤⣶⣶⣿⢿⢿⢿⡟⢻⣤⢑⢂ "
            f"⣾⣿⣿⡿⢟⣛⣻⣿⣿⣿⣦⣬⣙⣻⣿⣿⣷⣿⣿⢟⢝⢕⢕⢕⢕⢽⣿⣿⣷⣔ "
            f"⣿⣿⠵⠚⠉⢀⣀⣀⣈⣿⣿⣿⣿⣿⣿⣿⣿⣿⣗⢕⢕⢕⢕⢕⢕⣽⣿⣿⣿⣿ "
            f"⢷⣂⣠⣴⣾⡿⡿⡻⡻⣿⣿⣴⣿⣿⣿⣿⣿⣿⣷⣵⣵⣵⣷⣿⣿⣿⣿⣿⣿⡿ "
            f"⢌⠻⣿⡿⡫⡪⡪⡪⡪⣺⣿⣿⣿⣿⣿⠿⠿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠃ "
            f"⠣⡁⠹⡪⡪⡪⡪⣪⣾⣿⣿⣿⣿⠋⠐⢉⢍⢄⢌⠻⣿⣿⣿⣿⣿⣿⣿⣿⠏⠈ "
            f"⡣⡘⢄⠙⣾⣾⣾⣿⣿⣿⣿⣿⣿⡀⢐⢕⢕⢕⢕⢕⡘⣿⣿⣿⣿⣿⣿⠏⠠⠈ "
            f"⠌⢊⢂⢣⠹⣿⣿⣿⣿⣿⣿⣿⣿⣧⢐⢕⢕⢕⢕⢕⢅⣿⣿⣿⣿⡿⢋⢜⠠⠈ "
            f"⠄⠁⠕⢝⡢⠈⠻⣿⣿⣿⣿⣿⣿⣿⣷⣕⣑⣑⣑⣵⣿⣿⣿⡿⢋⢔⢕⣿⠠⠈ "
            f"⠨⡂⡀⢑⢕⡅⠂⠄⠉⠛⠻⠿⢿⣿⣿⣿⣿⣿⣿⣿⣿⡿⢋⢔⢕⢕⣿⣿⠠⠈ "
            f"⠄⠪⣂⠁⢕⠆⠄⠂⠄⠁⡀⠂⡀⠄⢈⠉⢍⢛⢛⢛⢋⢔⢕⢕⢕⣽⣿⣿⠠⠈"
        )

    @commands.command()
    async def weeb2(self, ctx: commands.Context):
        await ctx.send(
            f"⠄⠄⠄⢰⣧⣼⣯⠄⣸⣠⣶⣶⣦⣾⠄⠄⠄⠄⡀⠄⢀⣿⣿⠄⠄⠄⢸⡇⠄⠄"
            f"⠄⠄⠄⣾⣿⠿⠿⠶⠿⢿⣿⣿⣿⣿⣦⣤⣄⢀⡅⢠⣾⣛⡉⠄⠄⠄⠸⢀⣿⠄"
            f"⠄⠄⢀⡋⣡⣴⣶⣶⡀⠄⠄⠙⢿⣿⣿⣿⣿⣿⣴⣿⣿⣿⢃⣤⣄⣀⣥⣿⣿⠄"
            f"⠄⠄⢸⣇⠻⣿⣿⣿⣧⣀⢀⣠⡌⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠿⠿⣿⣿⣿⠄"
            f"⠄⢀⢸⣿⣷⣤⣤⣤⣬⣙⣛⢿⣿⣿⣿⣿⣿⣿⡿⣿⣿⡍⠄⠄⢀⣤⣄⠉⠋⣰"
            f"⠄⣼⣖⣿⣿⣿⣿⣿⣿⣿⣿⣿⢿⣿⣿⣿⣿⣿⢇⣿⣿⡷⠶⠶⢿⣿⣿⠇⢀⣤"
            f"⠘⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣽⣿⣿⣿⡇⣿⣿⣿⣿⣿⣿⣷⣶⣥⣴⣿⡗"
            f"⢀⠈⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠄"
            f"⢸⣿⣦⣌⣛⣻⣿⣿⣧⠙⠛⠛⡭⠅⠒⠦⠭⣭⡻⣿⣿⣿⣿⣿⣿⣿⣿⡿⠃⠄"
            f"⠘⣿⣿⣿⣿⣿⣿⣿⣿⡆⠄⠄⠄⠄⠄⠄⠄⠄⠹⠈⢋⣽⣿⣿⣿⣿⣵⣾⠃⠄"
            f"⠄⠘⣿⣿⣿⣿⣿⣿⣿⣿⠄⣴⣿⣶⣄⠄⣴⣶⠄⢀⣾⣿⣿⣿⣿⣿⣿⠃⠄⠄"
            f"⠄⠄⠈⠻⣿⣿⣿⣿⣿⣿⡄⢻⣿⣿⣿⠄⣿⣿⡀⣾⣿⣿⣿⣿⣛⠛⠁⠄⠄⠄"
            f"⠄⠄⠄⠄⠈⠛⢿⣿⣿⣿⠁⠞⢿⣿⣿⡄⢿⣿⡇⣸⣿⣿⠿⠛⠁⠄⠄⠄⠄⠄"
            f"⠄⠄⠄⠄⠄⠄⠄⠉⠻⣿⣿⣾⣦⡙⠻⣷⣾⣿⠃⠿⠋⠁⠄⠄⠄⠄⠄⢀⣠⣴"
            f"⣿⣿⣿⣶⣶⣮⣥⣒⠲⢮⣝⡿⣿⣿⡆⣿⡿⠃⠄⠄⠄⠄⠄⠄⠄⣠⣴⣿⣿⣿"
        )

    @commands.command()
    async def shark(self, ctx: commands.Context):
        await ctx.send(
            f"⢕⢕⢕⢕⢕⢕⢕⢕⢕⢕⢕⢕⢕⢕⢕⢕⢕⢕⢕⢕⢕⢕⠕⠕⠕⠕⢕⢕ "
            f"⢕⢕⢕⢕⢕⠕⠕⢕⢕⢕⢕⢕⢕⢕⢕⢕⢕⠕⠁⣁⣠⣤⣤⣤⣶⣦⡄⢑ "
            f"⢕⢕⢕⠅⢁⣴⣤⠀⣀⠁⠑⠑⠁⢁⣀⣀⣀⣀⣘⢻⣿⣿⣿⣿⣿⡟⢁⢔ "
            f"⢕⢕⠕⠀⣿⡁⠄⠀⣹⣿⣿⣿⡿⢋⣥⠤⠙⣿⣿⣿⣿⣿⡿⠿⡟⠀⢔⢕ "
            f"⢕⠕⠁⣴⣦⣤⣴⣾⣿⣿⣿⣿⣇⠻⣇⠐⠀⣼⣿⣿⣿⣿⣿⣄⠀⠐⢕⢕ "
            f"⠅⢀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⣶⣿⣿⣿⣿⣿⣿⣿⣿⣷⡄⠐⢕ "
            f"⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡄⠐ "
            f"⢄⠈⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡆ "
            f"⢕⢔⠀⠈⠛⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿ "
            f"⢕⢕⢄⠈⠳⣶⣶⣶⣤⣤⣤⣤⣭⡍⢭⡍⢨⣯⡛⢿⣿⣿⣿⣿⣿⣿⣿⣿ "
            f"⢕⢕⢕⢕⠀⠈⠛⠿⢿⣿⣿⣿⣿⣿⣦⣤⣿⣿⣿⣦⣈⠛⢿⢿⣿⣿⣿⣿ "
            f"⢕⢕⢕⠁⢠⣾⣶⣾⣭⣖⣛⣿⠿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡆⢸⣿⣿⣿⡟ "
            f"⢕⢕⠅⢀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠟⠈⢿⣿⣿⡇ "
            f"⢕⠕⠀⠼⠟⢉⣉⡙⠻⠿⢿⣿⣿⣿⣿⣿⡿⢿⣛⣭⡴⠶⠶⠂⠀⠿⠿⠇"
        )

    @commands.command()
    async def gotem(self, ctx: commands.Context):
        await ctx.send(
            f"⣿⣿⣿⣿⣿⣿⣿⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠛⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿"
            f"⣿⣿⣿⣿⣿⣿⣿⣿⣦⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⣄⡀⠀⢻⣿⣿⣿⣿⣿⣿⣿⣿"
            f"⣿⣿⣿⣿⣿⣿⣿⣿⣿⣇⠀⠀⠀⠀⠀⠀⠀⠸⣿⣿⣿⠃⢰⣿⣿⣿⣿⣿⣿⣿⣿"
            f"⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⣿⣿⣿⣿⣿⣿⣿⣿"
            f"⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡆⠀⠀⠀⠀⠀⠀⢶⣶⣶⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿"
            f"⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⢠⡀⠐⠀⠀⠀⠻⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿"
            f"⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡄⢸⣷⡄⠀⠣⣄⡀⠀⠉⠛⢿⣿⣿⣿⣿⣿⣿⣿"
            f"⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣇⠀⣿⣿⣦⠀⠹⣿⣷⣶⣦⣼⣿⣿⣿⣿⣿⣿⣿"
            f"⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣼⣿⣿⣿⣷⣄⣸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿"
            f"⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿"
            f"⣿⣿⣿⣿⡿⢛⡙⢻⠛⣉⢻⣉⢈⣹⣿⣿⠟⣉⢻⡏⢛⠙⣉⢻⣿⣿⣿⣿⣿⣿"
            f"⣿⣿⣿⣿⣇⠻⠃⣾⠸⠟⣸⣿⠈⣿⣿⣿⡀⠴⠞⡇⣾⡄⣿⠘⣿⣿⣿⣿⣿⣿"
            f"⣿⣿⣿⣿⣟⠛⣃⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣿⣿⣿⣿⣿⣿⣿⣿"
            f"⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿"
        )

    @commands.command()
    async def fuchat(self, ctx: commands.Context):
        await ctx.send(
            f"⠄⢸⣿⡟⠛⠛⠃⢸⣿⡇⠄⠄⣿⡇⠄⣼⣿⠟⠻⣿⣆⠄⣿⣿⢠⣾⣿⠋⠄⠄"
            f"⠄⢸⣿⣷⣶⣶⠄⢸⣿⡇⠄⠄⣿⡇⠄⣿⡏⠄⠄⠄⠄⠄⣿⣿⣿⣿⣇⠄⠄⠄"
            f"⠄⢸⣿⡇⠄⠄⠄⠘⣿⣧⣀⣰⣿⡇⠄⢿⣿⣀⣠⣿⡶⠄⣿⣿⠃⢹⣿⣆⠄⠄"
            f"⠄⠘⠛⠃⠄⠄⠄⠄⠘⠛⠛⠛⠋⠄⠄⠈⠛⠛⠛⠛⠁⠄⠛⠛⠄⠄⠛⠛⠃⠄"
            f"⠄⠄⠄⠄⢠⣤⡄⠄⠄⣤⣤⠄⢀⣠⣤⣄⡀⠄⢠⣤⡄⠄⠄⣤⣤⠄⠄⠄⠄⠄"
            f"⠄⠄⠄⠄⠄⢻⣿⣄⣼⣿⠃⣰⣿⠟⠛⢿⣿⡄⢸⣿⡇⠄⠄⣿⣿⠄⠄⠄⠄⠄"
            f"⠄⠄⠄⠄⠄⠄⠻⣿⡿⠁⠄⣿⣿⠄⠄⢸⣿⡇⢸⣿⡇⠄⠄⣿⣿⠄⠄⠄⠄⠄"
            f"⠄⠄⠄⠄⠄⠄⠄⣿⡇⠄⠄⠹⣿⣦⣤⣼⣿⠃⠄⣿⣷⣤⣴⣿⡏⠄⠄⠄⠄⠄"
            f"⠄⠄⠄⠄⠄⠄⠄⠛⠃⠄⠄⠄⠈⠛⠛⠋⠁⠄⠄⠈⠙⠛⠛⠉⠄⠄⠄⠄⠄⠄"
            f"⠄⠄⢀⣠⣤⣤⣄⡀⠄⣤⣤⠄⠄⣤⣤⠄⠄⠄⣤⣤⡄⠄⣤⣤⣤⣤⣤⣤⠄⠄"
            f"⠄⠄⣾⣿⠋⠙⠿⠗⠄⣿⣿⣀⣀⣿⣿⠄⠄⣸⣿⢿⣷⠄⠛⠛⣿⣿⠛⠛⠄⠄"
            f"⠄⠄⣿⣿⠄⠄⣀⠄⠄⣿⣿⠿⠿⣿⣿⠄⢠⣿⣏⣸⣿⡆⠄⠄⣿⣿⠄⠄⠄⠄"
            f"⠄⠄⠻⣿⣦⣴⣿⡟⠄⣿⣿⠄⠄⣿⣿⠄⣼⣿⠿⠿⢿⣿⡀⠄⣿⣿⠄⠄⠄⠄"
            f"⠄⠄⠈⠉⠉⠉⠄⠄⠉⠉⠄⠄⠉⠉⠄⠉⠉⠄⠄⠈⠉⠁⠄⠉⠉⠄⠄⠄⠄"
        )

    @commands.command()
    async def creeper(self, ctx: commands.Context):
        await ctx.send(
            f"✅✅✅✅✅✅✅✅✅✅✅✅ "
            f"✅✅✅✅✅✅✅✅✅✅✅✅ "
            f"✅✅⬛⬛⬛✅✅⬛⬛⬛✅✅ "
            f"✅✅⬛⬛⬛✅✅⬛⬛⬛✅✅ "
            f"✅✅✅✅✅⬛⬛✅✅✅✅✅ "
            f"✅✅✅⬛⬛⬛⬛⬛⬛✅✅✅ "
            f"✅✅✅⬛⬛⬛⬛⬛⬛✅✅✅ "
            f"✅✅✅⬛⬛✅✅⬛⬛✅✅✅ "
            f"✅✅✅✅✅✅✅✅✅✅✅✅"
        )

    @commands.command()
    async def timehascome(self, ctx: commands.Context):
        await ctx.send(
            f"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢤⣶⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ "
            f"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⡾⠿⢿⡀⠀⠀⠀⠀⣠⣶⣿⣷⠀⠀⠀⠀ "
            f"⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣦⣴⣿⡋⠀⠀⠈⢳⡄⠀⢠⣾⣿⠁⠈⣿⡆⠀⠀⠀ "
            f"⠀⠀⠀⠀⠀⠀⠀⣰⣿⣿⠿⠛⠉⠉⠁⠀⠀⠀⠹⡄⣿⣿⣿⠀⠀⢹⡇⠀⠀⠀ "
            f"⠀⠀⠀⠀⠀⣠⣾⡿⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⣰⣏⢻⣿⣿⡆⠀⠸⣿⠀⠀⠀ "
            f"⠀⠀⠀⢀⣴⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣾⣿⣿⣆⠹⣿⣷⠀⢘⣿⠀⠀⠀ "
            f"⠀⠀⢀⡾⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⣿⠋⠉⠛⠂⠹⠿⣲⣿⣿⣧⠀⠀ "
            f"⠀⢠⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⣿⣿⣿⣷⣾⣿⡇⢀⠀⣼⣿⣿⣿⣧⠀ "
            f"⠰⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⡘⢿⣿⣿⣿⠀ "
            f"⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⣷⡈⠿⢿⣿⡆ "
            f"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠛⠁⢙⠛⣿⣿⣿⣿⡟⠀⡿⠀⠀⢀⣿⡇ "
            f"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣶⣤⣉⣛⠻⠇⢠⣿⣾⣿⡄⢻⡇ "
            f"⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣦⣤⣾⣿⣿⣿⣿⣆⠁ "
            f" ⠀⠀⠀⠀🈵⠀YOUR TIME HAS COME 🈵⠀"
        )
