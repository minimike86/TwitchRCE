from typing import List

import twitchio
from twitchio import User, PartialUser
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

    async def __validate__(self, user_token: str):
        await self._http.validate(token=user_token)

    async def __esclient_init__(self, esclient: eventsub.EventSubClient, database: Database) -> None:
        """ start the esclient listening on specified port """
        try:
            self.loop.create_task(esclient.listen(port=settings.EVENTSUB_URI_PORT))
            print(f"Running EventSub server on [port={settings.EVENTSUB_URI_PORT}]")
        except Exception as e:
            print(e.with_traceback(tb=None))

        await self.delete_event_subscriptions(esclient=esclient)

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

    async def delete_event_subscriptions(self, esclient):
        """ before registering new event subscriptions remove old event subs """
        app_token = self.db.fetch_app_token()[0]['access_token']
        esclient._http.__init__(client=esclient, token=app_token)
        es_subs = await esclient._http.get_subscriptions()
        print(f"{len(es_subs)} event subs found")
        for es_sub in es_subs:
            await esclient._http.delete_subscription(es_sub)
            print(f"deleting event sub: {es_sub.id}")
        del es_sub
        del es_subs
        print(f"deleted all event subs.")

    async def event_ready(self):
        """ Bot is logged into IRC and ready to do its thing. """
        print(f'Logged into channel(s): {self.connected_channels}, as User: {self.nick} (ID: {self.user_id})')
        logins = [channel.name for channel in self.connected_channels]
        user_data = await self._http.get_users(token=self._http.app_token, ids=[], logins=logins)
        for user in user_data:
            user = await PartialUser(http=self._http, id=user['id'], name=user['login']).fetch()
            await user.channel.send(f'Logged into channel(s): {self.connected_channels}, as User: {self.nick} (ID: {self.user_id})')

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
