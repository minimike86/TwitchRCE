# import asyncio
#
# import twitchio
# from twitchio.ext import commands
# from twitchio.ext.eventsub import ChannelFollowData, EventSubClient
#
# import settings
#
#
# loop = asyncio.get_event_loop()
# asyncio.set_event_loop(loop)
#
#
# # twitchio Bot
# esbot = commands.Bot.from_client_credentials(client_id=settings.CLIENT_ID,
#                                              client_secret=settings.CLIENT_SECRET)
#
# # twitchio EventSub client
# # secret must be between 10 and 100 characters
# # TODO: randomise webhook_secret
# esclient: EventSubClient = EventSubClient(client=esbot,
#                                           webhook_secret='some_secret_string',
#                                           callback_route=settings.CALLBACK_ROUTE)
#
#
# class CustomBot(commands.Bot):
#     def __init__(self):
#         super().__init__(token=settings.CHAT_OAUTH_ACCESS_TOKEN,
#                          prefix='!',
#                          initial_channels=settings.INITIAL_CHANNELS)
#
#         # twitchio HTTP client
#         # self.http = TwitchHTTP(client=esbot,
#         #                        api_token=settings.APP2APP_CLIENT_CREDENTIALS_GRANT_FLOW,
#         #                        client_id=settings.CLIENT_ID,
#         #                        client_secret=settings.CLIENT_SECRET)
#
#         # Load cogs
#         from cogs.rce import RCECog
#         self.add_cog(RCECog(self))
#         from cogs.vip import VIPCog
#         self.add_cog(VIPCog(self))
#
#     async def __ainit__(self) -> None:
#         # get user who authenticated
#         users = await self.http.get_users(token=settings.APP2APP_CLIENT_CREDENTIALS_GRANT_FLOW,
#                                           ids=[],
#                                           logins=settings.INITIAL_CHANNELS)
#         self.broadcaster: twitchio.PartialUser = PartialUser(http=self.http,
#                                                              id=int(users[0]['id']),
#                                                              name=users[0]['login'])
#         print(f"Running chat bot as {self.broadcaster.name} [broadcaster_id={self.broadcaster.id}]")
#
#         # delete all event subscriptions
#         es_subs = await esclient._http.get_subscriptions()
#         print(f"{len(es_subs)} event subs found")
#         for es_sub in es_subs:
#             await esclient._http.delete_subscription(es_sub)
#             print(f"deleting event sub: {es_sub.id}")
#         print(f"deleted all event subs.")
#
#         # Docs: https://twitchio.dev/en/latest/exts/eventsub.html
#         # bot.loop.create_task(eventsub_client.listen(port=4000))
#         try:
#             print(f"Starting esclient with callback_route: {settings.CALLBACK_ROUTE} [port={settings.EVENTSUB_URI_PORT}]")
#             loop.create_task(esclient.listen(port=settings.EVENTSUB_URI_PORT))
#             print(f"Running EventSub server on {settings.CALLBACK_ROUTE}")
#         except Exception as e:
#             print(e.with_traceback(tb=None))
#
#         # Follow
#         try:
#             await esclient.subscribe_channel_follows(broadcaster=125444292)
#             print("subscribed to channel follow events")
#         except twitchio.HTTPException as http_error:
#             print(f"{http_error} - subscribe_channel_follows")
#             exit(0)
#
#         """
#             # Cheer
#             try:
#                 await self.esclient.subscribe_channel_cheers(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel cheer events")
#             except twitchio.HTTPException as http_error:
#                 print(f"{http_error} - subscribe_channel_cheers")
#
#             # Sub
#             try:
#                 await self.esclient.subscribe_channel_subscriptions(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel subscription events")
#                 await self.esclient.subscribe_channel_subscription_end(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel subscription end events")
#                 await self.esclient.subscribe_channel_subscription_gifts(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel subscription gift events")
#                 await self.esclient.subscribe_channel_subscription_messages(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel subscription message events")
#             except twitchio.HTTPException as http_error:
#                 print(f"{http_error} - subscribe_channel_subscriptions")
#
#             # Raid
#             try:
#                 await self.esclient.subscribe_channel_raid(to_broadcaster=self.broadcaster)
#                 print("subscribed to channel raid events")
#             except twitchio.HTTPException as http_error:
#                 print(f"{http_error} - subscribe_channel_raid")
#
#             # Ban
#             try:
#                 await self.esclient.subscribe_channel_bans(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel ban events")
#                 await self.esclient.subscribe_channel_unbans(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel unban events")
#             except twitchio.HTTPException as http_error:
#                 print(f"{http_error} - subscribe_channel_bans")
#
#             # Hype train
#             try:
#                 await self.esclient.subscribe_channel_hypetrain_begin(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel hypetrain begin events")
#                 await self.esclient.subscribe_channel_hypetrain_progress(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel hypetrain progress events")
#                 await self.esclient.subscribe_channel_hypetrain_end(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel hypetrain end events")
#             except twitchio.HTTPException as http_error:
#                 print(f"{http_error} - subscribe_channel_hypetrain_begin")
#
#             # Poll
#             try:
#                 await self.esclient.subscribe_channel_poll_begin(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel poll begin events")
#                 await self.esclient.subscribe_channel_poll_progress(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel poll progress events")
#                 await self.esclient.subscribe_channel_poll_end(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel poll end events")
#             except twitchio.HTTPException as http_error:
#                 print(f"{http_error} - subscribe_channel_poll_begin")
#
#             # Prediction
#             try:
#                 await self.esclient.subscribe_channel_prediction_begin(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel prediction begin events")
#                 await self.esclient.subscribe_channel_prediction_progress(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel prediction progress events")
#                 await self.esclient.subscribe_channel_prediction_lock(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel prediction lock events")
#                 await self.esclient.subscribe_channel_prediction_end(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel prediction end events")
#             except twitchio.HTTPException as http_error:
#                 print(f"{http_error} - subscribe_channel_prediction_begin")
#
#             # Goal
#             try:
#                 await self.esclient.subscribe_channel_goal_begin(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel goal begin events")
#                 await self.esclient.subscribe_channel_goal_progress(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel goal progress events")
#                 await self.esclient.subscribe_channel_goal_end(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel goal end events")
#             except twitchio.HTTPException as http_error:
#                 print(f"{http_error} - subscribe_channel_goal_begin")
#
#             # Redemption
#             try:
#                 await self.esclient.subscribe_channel_points_reward_added(broadcaster=self.broadcaster, reward_id='')
#                 print("subscribed to channel points reward_added events")
#                 await self.esclient.subscribe_channel_points_reward_removed(broadcaster=self.broadcaster, reward_id='')
#                 print("subscribed to channel points reward_removed events")
#                 await self.esclient.subscribe_channel_points_reward_updated(broadcaster=self.broadcaster, reward_id='')
#                 print("subscribed to channel points reward_updated events")
#                 await self.esclient.subscribe_channel_points_redeemed(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel points redeemed events")
#                 await self.esclient.subscribe_channel_points_redeem_updated(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel points redeem updated events")
#             except twitchio.HTTPException as http_error:
#                 print(f"{http_error} - subscribe_channel_points_reward_added")
#
#             # Stream Start/End
#             try:
#                 await self.esclient.subscribe_channel_stream_start(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel stream start events")
#                 await self.esclient.subscribe_channel_stream_end(broadcaster=self.broadcaster.id)
#                 print("subscribed to channel stream end events")
#             except twitchio.HTTPException as http_error:
#                 print(f"{http_error} - subscribe_channel_stream_start")
#
#         """
#
#     async def event_ready(self):
#         # Notify us when everything is ready!
#         print(f'Logged into channel(s): {self.connected_channels}, as User: {self.nick} (ID: {self.user_id})')
#
#     async def event_message(self, message: twitchio.Message):
#         # Messages with echo set to True are messages sent by the bot...
#         # For now, we just want to ignore them...
#         if message.echo:
#             return
#
#         # Print the contents of our message to console...
#         print('Bot: ', message.author.name, message.content)  # Print the contents of our message to console...
#
#         # Since we have commands and are overriding the default `event_message`
#         # We must let the bot know we want to handle and invoke our commands...
#         await self.handle_commands(message)
#
#     async def delete_all_custom_rewards(self):
#         """ At the start of the stream get any custom bot-made rewards if they are present. """
#         rewards = await self.http.get_rewards(broadcaster_id=self.broadcaster.id,
#                                               only_manageable=True,
#                                               token=settings.USER_IMPLICIT_GRANT_FLOW_ACCESS_TOKEN)
#         print(f"Got rewards: [{json.dumps(rewards)}]")
#         """ Then delete any redemptions that match a list of custom reward titles. """
#         custom_reward_titles = ["Kill My Shell", "VIP"]
#         if rewards is not None:
#             for reward in list(filter(lambda x: x["title"] in custom_reward_titles, rewards)):
#                 await self.http.delete_custom_reward(broadcaster_id=self.broadcaster.id,
#                                                      reward_id=reward["id"],
#                                                      token=settings.USER_IMPLICIT_GRANT_FLOW_ACCESS_TOKEN)
#                 print(f"Deleted reward: [id={reward['id']}][title={reward['title']}]")
#
#
# @esbot.event()
# async def event_eventsub_notification_stream_start(self, payload: StreamOnlineData) -> None:
#     print(f"Received StreamOnlineData event! [broadcaster.name={payload.broadcaster.name}][type={payload.type}][started_at={payload.started_at}]")
#     await self.delete_all_custom_rewards()
#     # TODO: if sci & tech then add kill my shell
#     await self.http.create_reward(broadcaster_id=self.broadcaster.id,
#                                   title="Kill My Shell",
#                                   cost=6666,
#                                   prompt="Immediately close any terminal I have open without warning!",
#                                   global_cooldown=5 * 60,
#                                   token=settings.USER_IMPLICIT_GRANT_FLOW_ACCESS_TOKEN)
#     # TODO: check for free VIP slots before added
#     await self.http.create_reward(broadcaster_id=self.broadcaster.id,
#                                   title="VIP",
#                                   cost=80085,
#                                   prompt="VIPs have the ability to equip a special chat badge and chat in slow, sub-only, or follower-only modes!",
#                                   global_cooldown=5 * 60,
#                                   token=settings.USER_IMPLICIT_GRANT_FLOW_ACCESS_TOKEN)
#     await self.broadcaster.channel.send(f'This stream is now online!')
#
#
# @esbot.event()
# async def event_eventsub_notification_stream_end(self, payload: StreamOfflineData) -> None:
#     print(f"Received StreamOfflineData event! [broadcaster.name={payload.broadcaster.name}]")
#     await self.delete_all_custom_rewards()
#     await self.broadcaster.channel.send(f'This stream is now offline!')
#     exit(0)
#
#
# @esbot.event()
# async def event_eventsub_notification_follow(self, payload: any) -> None:
#     payload: ChannelFollowData = payload.data
#     print('Received ChannelFollowData event!')
#     await self.broadcaster.channel.send(f'{payload.user.name} followed woo hoo! {payload.followed_at}!')
#
#
# @esbot.event()
# async def event_eventsub_notification_subscription(self, payload: any) -> None:
#     payload: ChannelSubscribeData = payload.data
#     print('Received ChannelSubscribeData event!')
#     await self.broadcaster.channel.send(f'{payload.user.name} subscribed with {payload.tier} {payload.is_gift}! ')
#
#
# @esbot.event()
# async def event_eventsub_notification_raid(self, payload: any) -> None:
#     payload: ChannelRaidData = payload.data
#     print('Received ChannelRaidData event!')
#     await self.broadcaster.channel.send(f'{payload.raider.name} raided the channel with {payload.viewer_count} viewers! ')
