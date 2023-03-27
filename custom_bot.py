import json
import re
import sqlite3
from typing import List

import twitchio
from twitchio import User, PartialUser, errors
from twitchio.ext import commands, eventsub, pubsub

import settings
from api.virustotal.virus_total_api import VirusTotalApiClient
from db.database import Database
from api.twitch.twitch_api_auth import TwitchApiAuth


class Bot(commands.Bot):
    """ Custom twitchio bot class """
    def __init__(self, user_token: str, initial_channels: list[str], eventsub_public_url: str, database: Database):
        super().__init__(token=user_token,
                         prefix='!',
                         initial_channels=initial_channels)
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
        from cogs.user_cog import UserCog
        self.add_cog(UserCog(self))

    async def update_bot_http_token(self):
        """ updates the bots http client token """
        bot_access_token_resultset = self.database.fetch_user_access_token(broadcaster_login=settings.BOT_USERNAME)
        self._http.token = bot_access_token_resultset['access_token']

    async def set_stream_marker(self, payload: eventsub.NotificationEvent, event_string: str):
        # create stream marker (Stream markers cannot be created when the channel is offline)
        # TODO: Look into AttributeError: 'ChannelRaidData' object has no attribute 'broadcaster'
        streams = await self._http.get_streams(user_ids=[payload.data.broadcaster.id])
        if len(streams) >= 1 and streams[0]['type'] == 'live':
            access_token_resultset = None
            if hasattr(payload.data, 'reciever'):
                access_token_resultset = self.database.fetch_user_access_token(broadcaster_id=payload.data.reciever.id)
            else:
                access_token_resultset = self.database.fetch_user_access_token(broadcaster_id=payload.data.broadcaster.id)
            access_token = [str(token) for token in access_token_resultset][0]
            await payload.data.broadcaster.create_marker(token=access_token,
                                                         description=event_string)

    async def __channel_broadcasters_init__(self):
        """ get broadcasters objects for every user_login, you need these to send messages """
        user_login_resultset = self.database.fetch_all_user_logins()
        self.user_logins = [row['broadcaster_login'] for row in user_login_resultset]
        for login in self.user_logins:
            print(f"Validating user token for {login}")
            await self.validate_token(login)

        user_data = await self._http.get_users(token=self._http.app_token, ids=[], logins=self.user_logins)
        broadcasters: List[PartialUser] = []
        try:
            for user in user_data:
                broadcasters.append(await PartialUser(http=self._http, id=user['id'], name=user['login']).fetch())
        except twitchio.errors.Unauthorized as error:
            print(f"Unauthorized: {error}")
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

        broadcasters: List[User] = await self.fetch_users(names=[settings.BOT_JOIN_CHANNEL])
        for broadcaster in broadcasters:
            print(f'Subscribing to events for {broadcaster.name}\'s channel.')

            try:
                """ create new event subscription for channel_follows event"""
                event = await self.esclient.subscribe_channel_follows_v2(broadcaster=broadcaster.id, moderator=broadcaster.id)
                print(f'Subscribed to channel_follows event for {broadcaster.name}\'s channel.')
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
        if len(self.connected_channels) == 0:
            """ Bot failed to join channel. """
            await self.join_channels(channels=[settings.BOT_JOIN_CHANNEL])

        if len(self.connected_channels) >= 1:
            """ Bot is logged into IRC and ready to do its thing. """
            print(f'Logged into channel(s): {self.connected_channels}, as User: {self.nick} (ID: {self.user_id})')
            logins = [channel.name for channel in self.connected_channels]
            # TODO: Handle potential twitchio.errors.HTTPException: Failed to reach Twitch API
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
        user_resultset = self.database.fetch_user(broadcaster_login=login)
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
            try:
                auth_validate = await self._http.validate(token=auth_result['access_token'])
                print(f"The refreshed user token for {login} is valid.")
                await self.update_bot_http_token()
                return auth_validate
            except errors.AuthenticationError:
                print(f"The refreshed user token for {login} is invalid.")

    async def add_kill_my_shell_redemption_reward(self, broadcaster: PartialUser):
        """ Adds channel point redemption that immediately closes the last terminal window that was opened without warning """
        channel = await self._http.get_channels(broadcaster_id=broadcaster.id)
        if int(channel[0]['game_id']) in [509670, 1469308723]:  # Science & Technology, Software and Game Development
            user_token_resultset = self.database.fetch_user_access_token(broadcaster_id=broadcaster.id)
            await self._http.create_reward(broadcaster_id=broadcaster.id,
                                           title="Kill My Shell",
                                           cost=6666,
                                           prompt="Immediately closes the last terminal window that was opened without warning!",
                                           global_cooldown=5 * 60,
                                           token=user_token_resultset['access_token'])

    async def add_vip_auto_redemption_reward(self, broadcaster: PartialUser):
        """ Adds channel point redemption that adds the user to the VIP list automatically """
        user_token_resultset = self.database.fetch_user_access_token(broadcaster_id=broadcaster.id)
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
        user_access_token_resultset = self.database.fetch_user_access_token(broadcaster_id=broadcaster.id)
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
        user_access_token_resultset = self.database.fetch_user_access_token(broadcaster_id=broadcaster.id)
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
                # TODO: Handle potential twitchio.errors.HTTPException: Failed to reach Twitch API
                await broadcaster.shoutout(token=user_access_token_resultset['access_token'],
                                           to_broadcaster_id=channel['broadcaster_id'],
                                           moderator_id=broadcaster.id)

    """
    BOT COMMANDS BELOW VVVVVVVV
    """

    @commands.command()
    async def add_channel_subs(self, ctx: commands.Context):
        user_resultset = self.database.fetch_user(broadcaster_login=ctx.channel.name)
        subs = await self._http.get_channel_subscriptions(token=user_resultset[0]['access_token'],
                                                          broadcaster_id=user_resultset[0]['broadcaster_id'])
        self.database.update_all_subs_inactive()
        for sub in subs:
            try:
                self.database.insert_sub_data(broadcaster_id=sub['broadcaster_id'], broadcaster_login=sub['broadcaster_login'],
                                              broadcaster_name=sub['broadcaster_name'],
                                              gifter_id=sub['gifter_id'], gifter_login=sub['gifter_login'],
                                              gifter_name=sub['gifter_name'], is_gift=sub['is_gift'],
                                              plan_name=sub['plan_name'], tier=sub['tier'], user_id=sub['user_id'],
                                              user_name=sub['user_name'], user_login=sub['user_login'], is_active=True)
            except sqlite3.IntegrityError:
                print(f"Row already exists")

    @commands.command()
    async def kill_everyone(self, ctx: commands.Context):
        """ invoke skynet """
        await ctx.send(f'Killing everyone... starting with {ctx.author.name}!')

    @commands.command()
    async def virustotal(self, ctx: commands.Context):
        """
        VirusTotal API Limits:
            Request rate	4 lookups / min
            Daily quota	    500 lookups / day
            Monthly quota	15.5 K lookups / month
        """
        param: str = str(ctx.message.content).split(' ')[1]
        vt = VirusTotalApiClient()
        if param == '-h' or param == '--h' or param == '-help' or param == '--help':
            await ctx.send(f'Usage: !virustotal <hash>'
                           f'This command checks a file hash against the VirusTotal database to determine if it is a known malicious file.'
                           f'Arguments:'
                           f'   <hash>  Required. The file hash to check against the VirusTotal database.'
                           f'Examples:'
                           f'   virustotal 83b79423cfea613fcb89c01f1717a852ea05e986aa3c3b1de17c314680b8d893'
                           f'   virustotal 6c0e6e35b9c9d1a25f1c92fb90f8fe03'
                           f'Options:'
                           f'   -h, --help    Show this help message and exit.')

        elif re.match(r'^(http(s)?(://)?)?(www\.)?([\w\d]{0,253})(\.)([\w\d]{2,})([/\w\d]*)$', param):
            """ type !virustotal <domain> to lookup a domain on virustotal """
            try:
                domain_report = await vt.get_url_report(url=param)
                report_output: list[str] = ['VirusTotal -> ']
                report_output.append(f'url: {domain_report.url}, ') if hasattr(domain_report, 'url') else None
                report_output.append(f'last_final_url: {domain_report.last_final_url}, ') if hasattr(domain_report, 'last_final_url') else None
                report_output.append(f'title: {domain_report.title}, ') if hasattr(domain_report, 'title') else None
                report_output.append(f'first_submission_date: {domain_report.first_submission_date}, ') if hasattr(domain_report, 'first_submission_date') else None
                report_output.append(f'last_analysis_stats["harmless"]: {domain_report.last_analysis_stats["harmless"]}, ') if hasattr(domain_report, 'last_analysis_stats') else None
                report_output.append(f'last_analysis_stats["malicious"]: {domain_report.last_analysis_stats["malicious"]}, ') if hasattr(domain_report, 'last_analysis_stats') else None
                report_output.append(f'total_votes["harmless"]: {domain_report.total_votes["harmless"]}, ') if hasattr(domain_report, 'total_votes') else None
                report_output.append(f'total_votes["malicious"]: {domain_report.total_votes["malicious"]}, ') if hasattr(domain_report, 'total_votes') else None
                report_output.append(f'times_submitted: {domain_report.times_submitted}!') if hasattr(domain_report, 'times_submitted') else None
                await ctx.send(''.join(report_output))
            except Exception as shitfuckedupyo:
                await ctx.send(f'There\'s no VirusTotal report for this URL! {shitfuckedupyo}')

        else:
            """ type !virustotal <hash> to lookup a hash on virustotal """
            try:
                file_report = await vt.get_file_report(hash_id=param)
                report_output: list[str] = ['VirusTotal -> ']
                report_output.append(f'meaningful_name: {file_report.meaningful_name}, ') if hasattr(file_report, 'meaningful_name') else None
                report_output.append(f'magic: {file_report.magic}, ') if hasattr(file_report, 'magic') else None
                report_output.append(f'popular_threat_classification: {file_report.popular_threat_classification["suggested_threat_label"]}, ') if hasattr(file_report, 'popular_threat_classification') else None
                report_output.append(f'first_seen_itw_date: {file_report.first_seen_itw_date}, ') if hasattr(file_report, 'first_seen_itw_date') else None
                report_output.append(f'last_analysis_stats["harmless"]: {file_report.last_analysis_stats["harmless"]}, ') if hasattr(file_report, 'last_analysis_stats') else None
                report_output.append(f'last_analysis_stats["malicious"]: {file_report.last_analysis_stats["malicious"]}, ') if hasattr(file_report, 'last_analysis_stats') else None
                report_output.append(f'total_votes["harmless"]: {file_report.total_votes["harmless"]}, ') if hasattr(file_report, 'total_votes') else None
                report_output.append(f'total_votes["malicious"]: {file_report.total_votes["malicious"]}, ') if hasattr(file_report, 'total_votes') else None
                report_output.append(f'times_submitted: {file_report.times_submitted}!') if hasattr(file_report, 'times_submitted') else None
                await ctx.send(''.join(report_output))
            except Exception as shitfuckedupyo:
                await ctx.send(f'There\'s no VirusTotal report for this hash! {shitfuckedupyo}')

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
    async def lurk(self, ctx: commands.Context):
        """ type !lurk to let the streamer know you're lurking """
        await ctx.send(f'{ctx.author.name} is watching the stream with the /silent flag!')

    @commands.command()
    async def raids(self, ctx: commands.Context):
        """ type !raids @username to print out how many raids you've received from the user """
        param_username = re.sub(r"^@", "", str(ctx.message.content).split(' ')[1])
        if len(param_username) >= 1:
            raider_login_resultset: sqlite3.Row = self.database.fetch_raids(raider_login=param_username.lower(), receiver_login=ctx.channel.name)
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
        """ type !shoutout <@username> to shout out a viewers channel """
        param_username = re.sub(r"^@", "", str(ctx.message.content).split(' ')[1])
        if len(param_username) >= 1:
            to_shoutout_user = await self._http.get_users(ids=[], logins=[param_username])
            to_shoutout_channel = await self._http.get_channels(broadcaster_id=to_shoutout_user[0]['id'])
            # TODO: Handle potential twitchio.errors.HTTPException: Failed to reach Twitch API
            # TODO: Handle IndexError: list index out of range if channel name is not in self.channel_broadcasters
            from_broadcaster: PartialUser = list(filter(lambda x: x.name == ctx.channel.name, self.channel_broadcasters))[0]
            await self.announce_shoutout(broadcaster=from_broadcaster, channel=to_shoutout_channel[0], color='blue')
