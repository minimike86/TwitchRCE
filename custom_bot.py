import json
import re
import sqlite3
from typing import List

import twitchio
from twitchio import User, PartialUser, errors
from twitchio.ext import commands, eventsub, pubsub

import settings
from db.database import Database
from twitch_api_auth import TwitchApiAuth


class Bot(commands.Bot):
    """ Custom twitchio bot class """
    def __init__(self, user_token: str, initial_channels: list[str], eventsub_public_url: str, database: Database):
        super().__init__(token=user_token,
                         prefix='!',
                         initial_channels=initial_channels)
        self.initial_channels = initial_channels
        self.database = database

        self.psclient: pubsub.PubSubPool = pubsub.PubSubPool(client=self)

        self.esclient: eventsub.EventSubClient = eventsub.EventSubClient(client=self,
                                                                         webhook_secret='some_secret_string',
                                                                         callback_route=f"{eventsub_public_url}")

        """ load commands from cogs """
        from cogs.rce import RCECog
        self.add_cog(RCECog(self))

        from cogs.vip import VIPCog
        self.add_cog(VIPCog(self))

    async def __channel_broadcasters_init__(self):
        """ get broadcasters objects for every user_login, you need these to send messages """
        user_login_resultset = self.database.fetch_all_user_logins()
        self.user_logins = [row['broadcaster_login'] for row in user_login_resultset]
        for login in self.user_logins:
            print(f"Validating user token for {login}")
            await self.validate_token(login)

        user_data = await self._http.get_users(token=self._http.app_token, ids=[], logins=self.user_logins)
        broadcasters: List[PartialUser] = []
        for user in user_data:
            broadcasters.append(await PartialUser(http=self._http, id=user['id'], name=user['login']).fetch())
        self.channel_broadcasters = broadcasters

    async def __validate__(self, user_token: str):
        validate_result = await self._http.validate(token=user_token)
        print(f"Validation complete: {validate_result}")

    async def __psclient_init__(self, user_token: str, channel_id: int) -> None:
        topics = [
            pubsub.channel_points(user_token)[channel_id],
        ]
        await self.psclient.subscribe_topics(topics)

    async def __esclient_init__(self) -> None:
        """ start the esclient listening on specified port """
        try:
            self.loop.create_task(self.esclient.listen(port=settings.EVENTSUB_URI_PORT))
            print(f"Running EventSub server on [port={settings.EVENTSUB_URI_PORT}]")
        except Exception as e:
            print(e.with_traceback(tb=None))

        await self.delete_event_subscriptions()

        broadcasters: List[User] = await self.fetch_users(names=self.initial_channels)
        for broadcaster in broadcasters:
            print(f'Subscribing to events for {broadcaster.name}\'s channel.')

            try:
                """ create new event subscription for channel_follows event"""
                await self.esclient.subscribe_channel_follows(broadcaster=broadcaster.id)
            except twitchio.HTTPException:
                print(f'Failed to subscribe to channel_follows event for {broadcaster.name}\'s channel.')

            try:
                """ create new event subscription for channel_cheers event """
                await self.esclient.subscribe_channel_cheers(broadcaster=broadcaster.id)
            except twitchio.HTTPException:
                print(f'Failed to subscribe to channel_cheers event for {broadcaster.name}\'s channel.')

            try:
                """ create new event subscription for channel_subscriptions event """
                await self.esclient.subscribe_channel_subscriptions(broadcaster=broadcaster.id)
            except twitchio.HTTPException:
                print(f'Failed to subscribe to channel_subscriptions event for {broadcaster.name}\'s channel.')

            try:
                """ create new event subscription for channel_raid event """
                await self.esclient.subscribe_channel_raid(to_broadcaster=broadcaster.id)
            except twitchio.HTTPException:
                print(f'Failed to subscribe to channel_raid event for {broadcaster.name}\'s channel.')

            try:
                """ create new event subscription for channel_stream_start event """
                await self.esclient.subscribe_channel_stream_start(broadcaster=broadcaster.id)
            except twitchio.HTTPException:
                print(f'Failed to subscribe to channel_stream_start event for {broadcaster.name}\'s channel.')

            try:
                """ create new event subscription for channel_stream_end event """
                await self.esclient.subscribe_channel_stream_end(broadcaster=broadcaster.id)
            except twitchio.HTTPException:
                print(f'Failed to subscribe to channel_stream_end event for {broadcaster.name}\'s channel.')

            # try:
            #     """ create new event subscription for channel_points_redeemed event """
            #     await self.esclient.subscribe_channel_points_reward_added(broadcaster=broadcaster.id, reward_id=)
            # except twitchio.HTTPException:
            #     print(f'Failed to subscribe to channel_points_redeemed event for {broadcaster.name}\'s channel.')

            # try:
            #     """ create new event subscription for channel_points_reward_updated event """
            #     await self.esclient.subscribe_channel_points_reward_updated(broadcaster=broadcaster.id, reward_id=)
            # except twitchio.HTTPException:
            #     print(f'Failed to subscribe to channel_points_reward_updated event for {broadcaster.name}\'s channel.')

            # try:
            #     """ create new event subscription for channel_points_reward_removed event """
            #     await self.esclient.subscribe_channel_points_reward_removed(broadcaster=broadcaster.id, reward_id=)
            # except twitchio.HTTPException:
            #     print(f'Failed to subscribe to channel_points_reward_removed event for {broadcaster.name}\'s channel.')

            # try:
            #     """ create new event subscription for channel_points_redeemed event """
            #     await self.esclient.subscribe_channel_points_redeemed(broadcaster=broadcaster.id)
            # except twitchio.HTTPException:
            #     print(f'Failed to subscribe to channel_points_redeemed event for {broadcaster.name}\'s channel.')

            # try:
            #     """ create new event subscription for channel_points_redeem_updated event """
            #     await self.esclient.subscribe_channel_points_redeem_updated(broadcaster=broadcaster.id)
            # except twitchio.HTTPException:
            #     print(f'Failed to subscribe to channel_points_redeem_updated event for {broadcaster.name}\'s channel.')

    async def delete_event_subscriptions(self):
        """ before registering new event subscriptions remove old event subs """
        app_token = self.database.fetch_app_token()[0]['access_token']
        self.esclient.client._http.token = app_token
        self.esclient._http.__init__(client=self.esclient, token=app_token)
        es_subs = await self.esclient._http.get_subscriptions()
        print(f"{len(es_subs)} event subs found")
        for es_sub in es_subs:
            await self.esclient._http.delete_subscription(es_sub)
            print(f"deleting event sub: {es_sub.id}")
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
        # TODO: if message content is a known follow bot account message then autoban the author
        await self.handle_commands(message)  # we have commands overriding the default `event_message`

    # check for any user logins and validate their access_tokens.
    # If invalid or missing then generate new tokens
    async def validate_token(self, login: str) -> any:
        """
        test a user token and if invalid prompt user to visit a url to generate a new token
        """
        user_resultset = self.database.fetch_user_from_login(login)
        user_data = [row for row in user_resultset][0]
        try:
            auth_validate = await self._http.validate(token=user_data['access_token'])
            print(f"The user token for {login} is valid.")
            return auth_validate
        except errors.AuthenticationError:
            # Try to use a refresh token to update the access token
            twitch_api_auth_http = TwitchApiAuth()
            auth_result = await twitch_api_auth_http.refresh_access_token(refresh_token=user_data['refresh_token'])
            self.database.insert_user_data(user_data['broadcaster_id'], user_data['broadcaster_login'], user_data['email'],
                                           auth_result['access_token'], auth_result['expires_in'],
                                           auth_result['refresh_token'], auth_result['scope'])
            print(f"Updated access and refresh token for {user_data['broadcaster_login']}")
            return auth_result

            # TODO: if tokens are missing use this code to obtain new tokens
            # # Get UserID via Authorization code grant flow
            # # https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#authorization-code-grant-flow
            # scope = "analytics:read:extensions analytics:read:games bits:read channel:edit:commercial channel:manage:broadcast channel:read:charity channel:manage:extensions channel:manage:moderators channel:manage:polls channel:manage:predictions channel:manage:raids channel:manage:redemptions channel:manage:schedule channel:manage:videos channel:read:editors channel:read:goals channel:read:hype_train channel:read:polls channel:read:predictions channel:read:redemptions channel:read:stream_key channel:read:subscriptions channel:read:vips channel:manage:vips clips:edit moderation:read moderator:manage:announcements moderator:manage:automod moderator:read:automod_settings moderator:manage:automod_settings moderator:manage:banned_users moderator:read:blocked_terms moderator:manage:blocked_terms moderator:manage:chat_messages moderator:read:chat_settings moderator:manage:chat_settings moderator:read:chatters moderator:read:followers moderator:read:shield_mode moderator:manage:shield_mode moderator:read:shoutouts moderator:manage:shoutouts user:edit user:edit:follows user:manage:blocked_users user:read:blocked_users user:read:broadcast user:manage:chat_color user:read:email user:read:follows user:read:subscriptions user:manage:whispers channel:moderate chat:edit chat:read whispers:read whispers:edit"
            # authorization_url = f"https://id.twitch.tv/oauth2/authorize?client_id={settings.CLIENT_ID}" \
            #                     f"&force_verify=true" \
            #                     f"&redirect_uri=http://localhost:3000/auth" \
            #                     f"&response_type=code" \
            #                     f"&scope={scope.replace(' ', '%20')}" \
            #                     f"&state={secrets.token_hex(16)}"
            # print("Launching auth site:", authorization_url)
            #
            # logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            # with ThreadingTCPServerWithStop(("0.0.0.0", 3000), CodeHandler) as tcpserver:
            #     logger.info(f"Serving on {tcpserver.server_address}...")
            #     tcpserver.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            #     if tcpserver.stop is not True:
            #         tcpserver.stop = False
            #         tcpserver.serve_forever(poll_interval=0.1)
            #     logger.info('Server stopped')
            #
            # twitch_api_auth = TwitchApiAuth()
            # auth_result = await twitch_api_auth.obtain_access_token(code=tcpserver.code,
            #                                                         redirect_uri='http://localhost:3000/auth')
            # http_client.token = auth_result['access_token']
            # users = await http_client.get_users(ids=[], logins=[], token=auth_result['access_token'])
            # db.insert_user_data(broadcaster_id=users[0]['id'], broadcaster_login=users[0]['login'],
            #                     email=users[0]['email'], access_token=auth_result['access_token'],
            #                     expires_in=auth_result['expires_in'], refresh_token=auth_result['refresh_token'],
            #                     scope=auth_result['scope'])

    async def add_kill_my_shell_redemption_reward(self, broadcaster: PartialUser):
        """ Adds channel point redemption that immediately closes the last terminal window that was opened without warning """
        channel = await self._http.get_channels(broadcaster_id=broadcaster.id)
        if int(channel[0]['game_id']) in [509670, 1469308723]:  # Science & Technology, Software and Game Development
            user_token_resultset = self.database.fetch_user_access_token_from_id(broadcaster.id)
            await self._http.create_reward(broadcaster_id=broadcaster.id,
                                           title="Kill My Shell",
                                           cost=6666,
                                           prompt="Immediately closes the last terminal window that was opened without warning!",
                                           global_cooldown=5 * 60,
                                           token=user_token_resultset['access_token'])

    async def add_vip_auto_redemption_reward(self, broadcaster: PartialUser):
        """ Adds channel point redemption that adds the user to the VIP list automatically """
        user_token_resultset = self.database.fetch_user_access_token_from_id(broadcaster.id)
        vips = await self._http.get_channel_vips(token=user_token_resultset['access_token'],
                                                 broadcaster_id=broadcaster.id,
                                                 first=100)
        if len(vips) < settings.MAX_VIP_SLOTS:
            await self._http.create_reward(broadcaster_id=broadcaster.id,
                                           title="VIP",
                                           cost=80085,
                                           prompt="VIPs have the ability to equip a special chat badge and bypass the chat limit in slow mode!",
                                           max_per_user=1,
                                           global_cooldown=5 * 60,
                                           token=user_token_resultset['access_token'])

    async def delete_all_custom_rewards(self, broadcaster: PartialUser):
        """ deletes all custom rewards (API limits deletes to those created by the bot)
            Requires a user access token that includes the channel:manage:redemptions scope. """
        user_access_token_resultset = self.database.fetch_user_access_token_from_id(broadcaster.id)
        rewards = await self._http.get_rewards(broadcaster_id=broadcaster.id,
                                               only_manageable=True,
                                               token=user_access_token_resultset['access_token'])
        print(f"Got rewards: [{json.dumps(rewards)}]")
        if rewards is not None:
            custom_reward_titles = ["Kill My Shell", "VIP"]
            for reward in list(filter(lambda x: x["title"] in custom_reward_titles, rewards)):
                await self._http.delete_custom_reward(broadcaster_id=broadcaster.id,
                                                      reward_id=reward["id"],
                                                      token=user_access_token_resultset['access_token'])
                print(f"Deleted reward: [id={reward['id']}][title={reward['title']}]")

    async def announce_shoutout(self, broadcaster: PartialUser, channel: any, color: str):
        """ Post a shoutout announcement to chat; color = blue, green, orange, purple, or primary """
        message = f"Please check out {channel['broadcaster_name']}\'s channel https://www.twitch.tv/{channel['broadcaster_login']}!"
        if not channel['game_name'] == '':
            message += f" They were last playing \'{channel['game_name']}\'."
        user_access_token_resultset = self.database.fetch_user_access_token_from_id(broadcaster.id)
        await self._http.post_chat_announcement(token=user_access_token_resultset['access_token'],
                                                broadcaster_id=broadcaster.id,
                                                message=message,
                                                moderator_id=broadcaster.id,
                                                # This ID must match the user ID in the user access token.
                                                color=color)  # blue green orange purple primary
        """ Perform a Twitch Shoutout command (https://help.twitch.tv/s/article/shoutouts?language=en_US). 
            The channel giving a Shoutout must be live AND you cannot shoutout the current streamer."""
        if channel['broadcaster_id'] != str(broadcaster.id):
            streams = await self._http.get_streams(user_ids=[broadcaster.id])
            if len(streams) >= 1 and streams[0]['type'] == 'live':
                await broadcaster.shoutout(token=user_access_token_resultset['access_token'],
                                           to_broadcaster_id=channel['broadcaster_id'],
                                           moderator_id=broadcaster.id)

    @commands.command()
    async def kill_everyone(self, ctx: commands.Context):
        """ invoke skynet """
        await ctx.send(f'Killing everyone... starting with {ctx.author.name}!')

    # TODO: add sound extensions commands https://twitchio.dev/en/latest/exts/sounds.html
    # MAKE AS A COG!!!
    @commands.command()
    async def ohlook(self, ctx: commands.Context):
        """ type !ohlook """
        if int(ctx.author.id) == 601591745 or int(ctx.author.id) == 125444292:
            await ctx.send(f'Oh look, it\'s the bitch!')
            await ctx.send(f'!so @stairsthetrashman')

    # TODO: add chatgpt commands https://github.com/openai/openai-python
    @commands.command()
    async def chatgpt(self, ctx: commands.Context):
        """ type !chatgpt <query> to ask chatgpt a question """
        await ctx.send(f'Hello {ctx.author.name}!')

    # TODO: add some discord commands https://discordpy.readthedocs.io/en/stable/
    @commands.command()
    async def discord(self, ctx: commands.Context):
        """ type !discord to do something with discord """
        await ctx.send(f'Hello {ctx.author.name}!')

    @commands.command()
    async def hello(self, ctx: commands.Context):
        """ type !hello to say hello to author """
        await ctx.send(f'Hello {ctx.author.name}!')

    @commands.command()
    async def raids(self, ctx: commands.Context):
        """ type !raids @username to print out how many raids you've received from the user """
        param_username = re.sub(r"^@", "", str(ctx.message.content).split(' ')[1])
        if len(param_username) >= 1:
            raider_login_resultset: sqlite3.Row = self.database.fetch_raids_from_login(raider_login=param_username)
            await ctx.send(f"{param_username} has raided the channel {len(raider_login_resultset)} times!")

    @commands.command()
    async def redemptions(self, ctx: commands.Context):
        """ type !redemptions to force the custom redemptions to load """
        broadcaster: PartialUser = list(filter(lambda x: x.name == ctx.channel.name, self.channel_broadcasters))[0]
        if int(ctx.author.id) == broadcaster.id or int(ctx.author.id) == 125444292:
            # Delete custom rewards before attempting to create new ones otherwise create_reward() will fail
            await self.delete_all_custom_rewards(broadcaster)
            # Add new custom rewards
            await self.add_kill_my_shell_redemption_reward(broadcaster)
            await self.add_vip_auto_redemption_reward(broadcaster)

    @commands.command(aliases=['so'])
    async def shoutout(self, ctx: commands.Context):
        """ type !shoutout to shout out a viewers channel """
        param_username = re.sub(r"^@", "", str(ctx.message.content).split(' ')[1])
        if len(param_username) >= 1:
            to_shoutout_user = await self._http.get_users(ids=[], logins=[param_username])
            to_shoutout_channel = await self._http.get_channels(broadcaster_id=to_shoutout_user[0]['id'])
            from_broadcaster: PartialUser = list(filter(lambda x: x.name == ctx.channel.name, self.channel_broadcasters))[0]
            await self.announce_shoutout(broadcaster=from_broadcaster, channel=to_shoutout_channel[0], color='blue')
