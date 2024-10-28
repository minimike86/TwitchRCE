import asyncio
from typing import List

import twitchio
from colorama import Fore, Style
from twitchio import AuthenticationError, User
from twitchio.ext import eventsub


class CustomEventSubClient(eventsub.EventSubClient):
    """
    ███████ ███████  ██████ ██      ██ ███████ ███    ██ ████████         ██ ███    ██ ██ ████████
    ██      ██      ██      ██      ██ ██      ████   ██    ██            ██ ████   ██ ██    ██
    █████   ███████ ██      ██      ██ █████   ██ ██  ██    ██            ██ ██ ██  ██ ██    ██
    ██           ██ ██      ██      ██ ██      ██  ██ ██    ██            ██ ██  ██ ██ ██    ██
    ███████ ███████  ██████ ███████ ██ ███████ ██   ████    ██    ███████ ██ ██   ████ ██    ██
    https://twitchio.dev/en/stable/exts/eventsub.html
    """

    def __init__(self, client, bot_oauth_token, webhook_secret, callback_route):
        super().__init__(
            client=client, webhook_secret=webhook_secret, callback_route=callback_route
        )
        self.bot_oauth_token = bot_oauth_token

    async def start_envsub(self, port: int):
        """start the esclient listening on specified port"""
        event_loop = asyncio.get_event_loop()
        event_loop.create_task(self.listen(port=port))
        print(
            f"{Fore.RED}Running EventSub server on "
            f"[{Fore.MAGENTA}port={port}{Fore.RED}].{Style.RESET_ALL}"
        )

    async def subscribe_channel_events(self, broadcaster, moderator):
        print(
            f"{Fore.RED}Subscribing to esclient events for "
            f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
        )

        try:
            """create new event subscription for channel_follows event"""
            await self.subscribe_channel_follows_v2(
                broadcaster=broadcaster.id, moderator=moderator.id
            )
            print(
                f"{Fore.RED}Subscribed to {Fore.MAGENTA}channel_follows{Fore.RED} event for "
                f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
            )
        except twitchio.HTTPException:
            print(
                f"{Fore.RED}Failed to subscribe to {Fore.MAGENTA}channel_follows{Fore.RED} event for "
                f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
            )

        try:
            """create new event subscription for channel_cheers event"""
            await self.subscribe_channel_cheers(broadcaster=broadcaster.id)
            print(
                f"{Fore.RED}Subscribed to {Fore.MAGENTA}channel_cheers{Fore.RED} event for "
                f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
            )
        except twitchio.HTTPException:
            print(
                f"{Fore.RED}Failed to subscribe to {Fore.MAGENTA}channel_cheers{Fore.RED} event for "
                f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
            )

        try:
            """create new event subscription for channel_subscriptions event"""
            await self.subscribe_channel_subscriptions(broadcaster=broadcaster.id)
            print(
                f"{Fore.RED}Subscribed to {Fore.MAGENTA}channel_subscriptions{Fore.RED} event for "
                f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
            )
        except twitchio.HTTPException:
            print(
                f"{Fore.RED}Failed to subscribe to {Fore.MAGENTA}channel_subscriptions{Fore.RED} event for "
                f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
            )

        try:
            """create new event subscription for channel_raid event"""
            await self.subscribe_channel_raid(to_broadcaster=broadcaster.id)
            print(
                f"{Fore.RED}Subscribed to {Fore.MAGENTA}channel_raid{Fore.RED} event for "
                f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
            )
        except twitchio.HTTPException:
            print(
                f"{Fore.RED}Failed to subscribe to {Fore.MAGENTA}channel_raid{Fore.RED} event for "
                f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
            )

        try:
            """create new event subscription for channel_stream_start event"""
            await self.subscribe_channel_stream_start(broadcaster=broadcaster.id)
            print(
                f"{Fore.RED}Subscribed to {Fore.MAGENTA}channel_stream_start{Fore.RED} event for {Fore.MAGENTA}"
                f"{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
            )
        except twitchio.HTTPException:
            print(
                f"{Fore.RED}Failed to subscribe to {Fore.MAGENTA}channel_stream_start{Fore.RED} event for "
                f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
            )

        try:
            """create new event subscription for channel_stream_end event"""
            await self.subscribe_channel_stream_end(broadcaster=broadcaster.id)
            print(
                f"{Fore.RED}Subscribed to {Fore.MAGENTA}channel_stream_end{Fore.RED} event for {Fore.MAGENTA}"
                f"{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
            )
        except twitchio.HTTPException:
            print(
                f"{Fore.RED}Failed to subscribe to {Fore.MAGENTA}channel_stream_end{Fore.RED} event for "
                f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
            )

        try:
            """create new event subscription for channel_charity_donate event"""
            await self.subscribe_channel_charity_donate(broadcaster=broadcaster.id)
            print(
                f"{Fore.RED}Subscribed to {Fore.MAGENTA}channel_charity_donate{Fore.RED} event for {Fore.MAGENTA}"
                f"{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
            )
        except twitchio.HTTPException:
            print(
                f"{Fore.RED}Failed to subscribe to {Fore.MAGENTA}channel_stream_end{Fore.RED} event for "
                f"{Fore.MAGENTA}{broadcaster.name}{Fore.RED}'s channel.{Style.RESET_ALL}"
            )

    async def delete_all_event_subscriptions(self):
        """before registering new event subscriptions remove old event subs"""
        self.client._http.token = self.bot_oauth_token
        self.client._http.__init__(client=self, token=self.bot_oauth_token)
        try:
            es_subs = await self.client._http.get_subscriptions()
            print(
                f"{Fore.RED}Found {Fore.MAGENTA}{len(es_subs)}{Fore.RED} event subscription(s).{Style.RESET_ALL}"
            )
            for es_sub in es_subs:
                await self.client._http.delete_subscription(es_sub)
                print(
                    f"{Fore.RED}Deleting the event subscription with id: "
                    f"{Fore.MAGENTA}{es_sub.id}{Fore.RED}.{Style.RESET_ALL}"
                )
        except AuthenticationError as error:
            print(f"{Fore.RED}AuthenticationError: {error}{Fore.RED}.{Style.RESET_ALL}")
            raise AuthenticationError

    async def delete_event_subscriptions(self, broadcasters: List[User]):
        """before registering new event subscriptions remove old event subs"""
        self.client._http.__init__(client=self, token=self.bot_oauth_token)
        es_subs = await self.client._http.get_subscriptions()
        print(
            f"{Fore.RED}Found {Fore.MAGENTA}{len(es_subs)}{Fore.RED} event subscription(s).{Style.RESET_ALL}"
        )
        for es_sub in es_subs:
            if (
                "broadcaster_user_id" in es_sub.condition
                and int(es_sub.condition["broadcaster_user_id"]) == broadcasters[0].id
            ) or (
                "to_broadcaster_user_id" in es_sub.condition
                and int(es_sub.condition["to_broadcaster_user_id"])
                == broadcasters[0].id
            ):
                await self.client._http.delete_subscription(es_sub)
                print(
                    f"{Fore.RED}Deleting the event subscription with id: "
                    f"{Fore.MAGENTA}{es_sub.id}{Fore.RED} for channel "
                    f"{Fore.MAGENTA}{broadcasters[0].name}{Fore.RED}.{Style.RESET_ALL}"
                )
