import json
from typing import List

import twitchio
from twitchio import User, PartialUser, errors
from twitchio.ext import commands, eventsub

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
        await self.handle_commands(message)  # we have commands overriding the default `event_message`

    async def event_eventsub_notification_follow(self, payload: eventsub.NotificationEvent) -> None:
        """ event triggered when someone follows the channel """
        print(f'Received follow event! {payload.data.user.name} [{payload.data.user.id}]')
        await self.get_channel(payload.data.broadcaster.name).send(
            f'Thank you {payload.data.user.name} for following the channel!')

    async def kill_everyone(self):
        """ invoke skynet """
        pass

    async def event_eventsub_notification_cheer(self, payload: eventsub.NotificationEvent) -> None:
        """ event triggered when someone cheers in the channel """
        event_string = ""
        if payload.data.is_anonymous:
            event_string = f"Received cheer event from anonymous, " \
                           f"cheered {payload.data.bits} bits, " \
                           f"message '{payload.data.message}'."
        else:
            event_string = f"Received cheer event from {payload.data.user.name} [{payload.data.user.id}], " \
                           f"cheered {payload.data.bits} bits, " \
                           f"message '{payload.data.message}'."
        print(event_string)
        # create stream marker (Stream markers cannot be created when the channel is offline)
        streams = await self._http.get_streams(user_ids=[payload.data.broadcaster.id])
        if len(streams) >= 1 and streams[0].type == 'live':
            row = self.database.fetch_user_access_token_from_id(payload.data.broadcaster.id)
            await payload.data.broadcaster.create_marker(token=row['access_token'],
                                                         description=event_string)
        if not payload.data.is_anonymous:
            # Get cheerer info
            channel = await self._http.get_channels(broadcaster_id=payload.data.user.id)
            clips = await self._http.get_clips(broadcaster_id=payload.data.user.id)
            # Acknowledge raid and reply with a channel bio
            await self.get_channel(payload.data.broadcaster.name).send(
                f"Thank you @{channel[0]['broadcaster_login']} for cheering {payload.data.bits} bits!")
            # shoutout the subscriber
            if len(clips) >= 1:
                """ check if sub is a streamer with clips on their channel and shoutout with clip player """
                await self.get_channel(payload.data.broadcaster.name).send(f"!so {channel[0]['broadcaster_login']}")
                await self.announce_shoutout(broadcaster=payload.data.broadcaster, channel=channel[0], color='green')
            else:
                """ shoutout without clip player """
                await self.announce_shoutout(broadcaster=payload.data.broadcaster, channel=channel[0], color='green')

    async def event_eventsub_notification_subscription(self, payload: eventsub.NotificationEvent) -> None:
        """ event triggered when someone subscribes the channel """
        print(f"Received subscription event from {payload.data.user.name} [{payload.data.user.id}], "
              f"with tier {payload.data.tier / 1000} sub. {'[GIFTED]' if payload.data.is_gift else ''}")
        # create stream marker (Stream markers cannot be created when the channel is offline)
        streams = await self._http.get_streams(user_ids=[payload.data.broadcaster.id])
        if len(streams) >= 1 and streams[0]['type'] == 'live':
            access_token = self.database.fetch_user_access_token_from_id(payload.data.broadcaster.id)
            await payload.data.broadcaster.create_marker(token=access_token,
                                                         description=f"Received subscription event from {payload.data.user.name} [{payload.data.user.id}], "
                                                                     f"with tier {payload.data.tier / 1000} sub. {'[GIFTED]' if payload.data.is_gift else ''}")
        # Get subscriber info
        channel = await self._http.get_channels(broadcaster_id=payload.data.user.id)
        clips = await self._http.get_clips(broadcaster_id=payload.data.user.id)
        # Acknowledge raid and reply with a channel bio
        if len(channel) >= 1:
            await self.get_channel(payload.data.broadcaster.name).send(
                f"Thank you @{channel[0]['broadcaster_login']} for the tier {payload.data.tier / 1000} subscription!")
        # shoutout the subscriber
        if len(clips) >= 1:
            """ check if sub is a streamer with clips on their channel and shoutout with clip player """
            await self.get_channel(payload.data.broadcaster.name).send(f"!so {channel[0]['broadcaster_login']}")
            await self.announce_shoutout(broadcaster=payload.data.broadcaster, channel=channel[0], color='green')
        else:
            """ shoutout without clip player """
            await self.announce_shoutout(broadcaster=payload.data.broadcaster, channel=channel[0], color='green')

    async def event_eventsub_notification_raid(self, payload: eventsub.NotificationEvent) -> None:
        """ event triggered when someone raids the channel """
        print(f"Received raid event from {payload.data.raider.name} [{payload.data.raider.id}], "
              f"with {payload.data.viewer_count} viewers!")
        broadcaster = list(filter(lambda x: x.id == payload.data.reciever.id, self.channel_broadcasters))[0]
        # create stream marker (Stream markers cannot be created when the channel is offline)
        streams = await self._http.get_streams(user_ids=[payload.data.reciever.id])
        if len(streams) >= 1 and streams[0]['type'] == 'live':
            access_token = self.database.fetch_user_access_token_from_id(payload.data.broadcaster.id)
            await broadcaster.create_marker(token=access_token,
                                            description=f"Received raid event from {payload.data.raider.name} [{payload.data.raider.id}], "
                                                        f"with {payload.data.viewer_count} viewers!")
        # Get raider info
        channel = await self._http.get_channels(broadcaster_id=payload.data.raider.id)
        clips = await self._http.get_clips(broadcaster_id=payload.data.raider.id)
        # Acknowledge raid and reply with a channel bio
        broadcaster_user = await self._http.get_users(ids=[payload.data.reciever.id], logins=[])
        await broadcaster.channel.send(f"TombRaid TombRaid TombRaid WELCOME RAIDERS!!! "
                                       f"Thank you @{channel[0]['broadcaster_login']} for trusting me with your community! "
                                       f"My name is {broadcaster_user[0]['display_name']}, {broadcaster_user[0]['description']}")
        # shoutout the raider
        if len(clips) >= 1:
            """ check if raider is a streamer with clips on their channel and shoutout with clip player """
            await broadcaster.channel.send(f"!so {channel[0]['broadcaster_login']}")
            await self.announce_shoutout(broadcaster=broadcaster, channel=channel[0], color='orange')
        else:
            """ shoutout without clip player """
            await self.announce_shoutout(broadcaster=broadcaster, channel=channel[0], color='orange')

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

    async def event_eventsub_notification_stream_start(self, payload: eventsub.NotificationEvent) -> None:
        """ event triggered when stream goes live """
        print(
            f"Received StreamOnlineData event! [broadcaster.name={payload.data.broadcaster.name}][type={payload.data.type}][started_at={payload.data.started_at}]")

        # Delete custom rewards before attempting to create new ones otherwise create_reward() will fail
        await self.delete_all_custom_rewards(payload.data.broadcaster)

        # Add new custom rewards
        await self.add_kill_my_shell_redemption_reward(payload.data.broadcaster)
        await self.add_vip_auto_redemption_reward(payload.data.broadcaster)

        # GET THE CHANNEL DATA BECAUSE TWITCHIO IS A PIECE OF FUCKING SHIT
        channel = await self._http.get_channels(broadcaster_id=payload.data.broadcaster.id)
        await channel.send(f'This stream is now online!')

    async def add_kill_my_shell_redemption_reward(self, broadcaster: PartialUser):
        """ Adds channel point redemption that immediately closes the last terminal window that was opened without warning """
        channel = await self._http.get_channels(broadcaster_id=broadcaster.id)
        if channel[0]['game_id'] in [509670, 1469308723]:  # Science & Technology, Software and Game Development
            row = self.database.fetch_user_access_token_from_id(broadcaster.id)
            await self._http.create_reward(broadcaster_id=broadcaster.id,
                                           title="Kill My Shell",
                                           cost=6666,
                                           prompt="Immediately closes the last terminal window that was opened without warning!",
                                           global_cooldown=5 * 60,
                                           token=row['access_token'])

    async def add_vip_auto_redemption_reward(self, broadcaster: PartialUser):
        """ Adds channel point redemption that adds the user to the VIP list automatically """
        row = self.database.fetch_user_access_token_from_id(broadcaster.id)
        vips = await self._http.get_channel_vips(token=row['access_token'],
                                                 broadcaster_id=broadcaster.id,
                                                 first=100)
        if len(vips) < settings.MAX_VIP_SLOTS:
            access_token = self.database.fetch_user_access_token_from_id(broadcaster.id)
            await self._http.create_reward(broadcaster_id=broadcaster.id,
                                           title="VIP",
                                           cost=80085,
                                           prompt="VIPs have the ability to equip a special chat badge and chat in slow, sub-only, or follower-only modes!",
                                           max_per_user=1,
                                           global_cooldown=5 * 60,
                                           token=row['access_token'])

    async def delete_all_custom_rewards(self, broadcaster: PartialUser):
        """ deletes all custom rewards (API limits deletes to those created by the bot)
            Requires a user access token that includes the channel:manage:redemptions scope. """
        row = self.database.fetch_user_access_token_from_id(broadcaster.id)
        rewards = await self._http.get_rewards(broadcaster_id=broadcaster.id,
                                               only_manageable=True,
                                               token=row['access_token'])
        print(f"Got rewards: [{json.dumps(rewards)}]")
        if rewards is not None:
            custom_reward_titles = ["Kill My Shell", "VIP"]
            for reward in list(filter(lambda x: x["title"] in custom_reward_titles, rewards)):
                await self._http.delete_custom_reward(broadcaster_id=broadcaster.id,
                                                      reward_id=reward["id"],
                                                      token=row['access_token'])
                print(f"Deleted reward: [id={reward['id']}][title={reward['title']}]")

    async def announce_shoutout(self, broadcaster: PartialUser, channel: any, color: str):
        """ Post a shoutout announcement to chat; color = blue, green, orange, purple, or primary """
        # TODO: handle blank game_name
        user_access_token_resultset = self.database.fetch_user_access_token_from_id(broadcaster.id)
        await self._http.post_chat_announcement(token=user_access_token_resultset['access_token'],
                                                broadcaster_id=broadcaster.id,
                                                message=f"Please check out {channel['broadcaster_name']}\'s channel https://www.twitch.tv/{channel['broadcaster_login']}! "
                                                         f"They were last playing \'{channel['game_name']}\'.",
                                                moderator_id=broadcaster.id,
                                                # This ID must match the user ID in the user access token.
                                                color=color)  # blue green orange purple primary
        """ Perform a Twitch Shoutout command (https://help.twitch.tv/s/article/shoutouts?language=en_US). 
            The channel giving a Shoutout must be live. """
        streams = await self._http.get_streams(user_ids=[broadcaster.id])
        if len(streams) >= 1 and streams[0]['type'] == 'live':
            await broadcaster.shoutout(token=user_access_token_resultset['access_token'],
                                       to_broadcaster_id=channel['broadcaster_id'],
                                       moderator_id=broadcaster.id)

    # TODO: add chatgpt commands https://github.com/openai/openai-python
    # TODO: add some discord commands https://discordpy.readthedocs.io/en/stable/

    @commands.command()
    async def hello(self, ctx: commands.Context):
        """ type !hello to say hello to author """
        await ctx.send(f'Hello {ctx.author.name}!')

    @commands.command(aliases=['so'])
    async def shoutout(self, ctx: commands.Context):
        """ type !shoutout to shout out a viewers channel """
        param_username = str(ctx.message.content).split(' ')[1]
        to_shoutout_user = await self._http.get_users(ids=[], logins=[param_username])
        to_shoutout_channel = await self._http.get_channels(broadcaster_id=to_shoutout_user[0]['id'])
        from_broadcaster: PartialUser = list(filter(lambda x: x.name == ctx.channel.name, self.channel_broadcasters))[0]
        await self.announce_shoutout(broadcaster=from_broadcaster, channel=to_shoutout_channel[0], color='blue')
