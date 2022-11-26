import asyncio
import os

import aiohttp
from twitchio.ext import commands

import settings

client_id = settings.TWITCH_CLIENT_ID
client_secret = settings.TWITCH_CLIENT_SECRET
oauth = settings.TWITCH_CHAT_OAUTH
prefix = '!'
channels = ['msec']


class Bot(commands.Bot):

    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...
        super().__init__(token=oauth, prefix=prefix, initial_channels=channels)

        self.loop = asyncio.get_event_loop()

        # Constants
        self.char_limit = self.character_limit = 500
        self.aiohttp_session = None

        # Load cogs
        for file in sorted(os.listdir("cogs")):
            if file.endswith(".py"):
                self.load_module("cogs." + file[:-3])

    async def event_ready(self):
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')

        # Initialize aiohttp Client Session
        if not self.aiohttp_session:
            self.aiohttp_session = aiohttp.ClientSession(loop=self.loop)

    async def event_message(self, message):
        # Messages with echo set to True are messages sent by the bot...
        # For now we just want to ignore them...
        if message.echo:
            return
        print('Bot: ', message.content)  # Print the contents of our message to console...

        # Since we have commands and are overriding the default `event_message`
        # We must let the bot know we want to handle and invoke our commands...
        await self.handle_commands(message)

    @commands.command()
    async def hello(self, ctx: commands.Context):
        # Send a hello back!
        await ctx.send(f'Hello {ctx.author.name}!')
