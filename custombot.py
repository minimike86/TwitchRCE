from typing import List

import twitchio
from twitchio import User
from twitchio.ext import commands, eventsub

import settings
from db.database import Database


class Bot(commands.Bot):
    """ Custom twitchio bot class """
    def __init__(self, user_token: str, initial_channels: list[str], db: Database):
        super().__init__(token=user_token,
                         prefix='!',
                         initial_channels=initial_channels)
        self.initial_channels = initial_channels
        self.db = db

        """ load commands from cogs """
        from cogs.rce import RCECog
        self.add_cog(RCECog(self))

        from cogs.vip import VIPCog
        self.add_cog(VIPCog(self))

    async def __esclient_init__(self, esclient: eventsub.EventSubClient, database: Database) -> None:
        """ start the esclient listening on specified port """
        try:
            self.loop.create_task(esclient.listen(port=settings.EVENTSUB_URI_PORT))
            print(f"Running EventSub server on [port={settings.EVENTSUB_URI_PORT}]")
        except Exception as e:
            print(e.with_traceback(tb=None))

        """ before registering new event subscriptions remove old event subs """
        esclient._http.__init__(client=esclient, token=self.db.fetch_app_token()[0]['access_token'])
        es_subs = await esclient._http.get_subscriptions()
        print(f"{len(es_subs)} event subs found")
        for es_sub in es_subs:
            await esclient._http.delete_subscription(es_sub)
            print(f"deleting event sub: {es_sub.id}")
        print(f"deleted all event subs.")

        broadcasters: List[User] = await self.fetch_users(names=self.initial_channels)
        for broadcaster in broadcasters:
            print(f'Subscribing to events for {broadcaster.name}\'s channel.')

            try:
                """ create new event subscription for channel_follows event"""
                await esclient.subscribe_channel_follows(broadcaster=broadcaster.id)
            except twitchio.HTTPException:
                print(f'Failed to subscribe to channel_follows event for {broadcaster.name}\'s channel.')

            try:
                """ create new event subscription for channel_cheers event """
                await esclient.subscribe_channel_cheers(broadcaster=broadcaster.id)
            except twitchio.HTTPException:
                print(f'Failed to subscribe to channel_cheers event for {broadcaster.name}\'s channel.')

            try:
                """ create new event subscription for channel_subscriptions event """
                await esclient.subscribe_channel_subscriptions(broadcaster=broadcaster.id)
            except twitchio.HTTPException:
                print(f'Failed to subscribe to channel_subscriptions event for {broadcaster.name}\'s channel.')

            try:
                """ create new event subscription for channel_raid event """
                await esclient.subscribe_channel_raid(to_broadcaster=broadcaster.id)
            except twitchio.HTTPException:
                print(f'Failed to subscribe to channel_raid event for {broadcaster.name}\'s channel.')

            try:
                """ create new event subscription for channel_stream_start event """
                await esclient.subscribe_channel_stream_start(broadcaster=broadcaster.id)
            except twitchio.HTTPException:
                print(f'Failed to subscribe to channel_stream_start event for {broadcaster.name}\'s channel.')

    async def event_ready(self):
        """ Bot is logged into IRC and ready to do its thing. """
        print(f'Logged into channel(s): {self.connected_channels}, as User: {self.nick} (ID: {self.user_id})')

    async def event_message(self, message: twitchio.Message):
        """ Messages with echo set to True are messages sent by the bot. ignore them. """
        if message.echo:
            return
        print('Bot: ', message.author.name, message.content)  # Print the contents of our message to console...
        await self.handle_commands(message)  # we have commands overriding the default `event_message`

    @commands.command()
    async def hello(self, ctx: commands.Context):
        """ type !hello to say hello to author """
        await ctx.send(f'Hello {ctx.author.name}!')
