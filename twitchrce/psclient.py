import logging
from typing import TYPE_CHECKING, List

import twitchio
from cogs.rce import RCECog as RCE_Cog
from cogs.vip import VIPCog as VIP_Cog
from colorama import Fore, Style
from twitchio import Chatter, Client, PartialChatter, User
from twitchio.ext import pubsub
from twitchio.ext.commands import Cog

if TYPE_CHECKING:
    from twitchrce.custom_bot import CustomBot

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class CustomPubSubClient(Client):
    """
    ██████  ███████  ██████ ██      ██ ███████ ███    ██ ████████         ██ ███    ██ ██ ████████
    ██   ██ ██      ██      ██      ██ ██      ████   ██    ██            ██ ████   ██ ██    ██
    ██████  ███████ ██      ██      ██ █████   ██ ██  ██    ██            ██ ██ ██  ██ ██    ██
    ██           ██ ██      ██      ██ ██      ██  ██ ██    ██            ██ ██  ██ ██ ██    ██
    ██      ███████  ██████ ███████ ██ ███████ ██   ████    ██    ███████ ██ ██   ████ ██    ██
    https://twitchio.dev/en/stable/exts/pubsub.html
    """

    def __init__(self, bot: "CustomBot", users_channel_id: int, bot_oauth_token: str):
        super().__init__(token=bot_oauth_token)
        self.bot = bot
        self.client = twitchio.Client(token=bot_oauth_token)
        self.users_channel_id: int = users_channel_id
        self.users_oauth_token: str = bot_oauth_token
        self.pubsub = CustomPubSubPool(self)
        self.topics = [
            pubsub.channel_points(self.users_oauth_token)[self.users_channel_id],
            pubsub.bits(self.users_oauth_token)[self.users_channel_id],
        ]

        @self.client.event()
        async def event_pubsub_bits(event: pubsub.PubSubBitsMessage):
            print(f"Bits donated by {event.user.name}: {event.bits_used}")
            pass  # do stuff on bit redemptions

        @self.client.event()
        async def event_pubsub_channel_points(event: pubsub.PubSubChannelPointsMessage):
            # Log redemption request - reward: CustomReward, user: PartialUser
            logger.info(
                f"{Fore.RED}[PubSub][ChannelPoints]: {event.reward.id}, {event.reward.title}, {event.reward.cost} | "
                f"User: {event.user.id}, {event.user.name}{Style.RESET_ALL}"
            )

            # Check if reward can be redeemed at this time
            if not event.reward.paused and event.reward.enabled:
                """We have to check redemption names as id's are randomly allocated when redemption is added"""

                if event.reward.title == "Kill My Shell" and (
                    self.bot.config.get_bot_config()
                    .get("bot_features")
                    .get("cogs")
                    .get("rce_cog")
                    .get("enable_rce_cog")
                ):
                    broadcaster: User = (
                        await self.fetch_users(ids=[event.channel_id])
                    )[0]
                    chatter: Chatter | PartialChatter = broadcaster.channel.get_chatter(
                        name=event.user.name
                    )
                    cog: RCE_Cog | Cog = self.bot.get_cog(name="RCE_Cog")
                    await cog.kill_my_shell(
                        broadcaster=broadcaster,
                        chatter=chatter,
                        event=event,
                    )

                if event.reward.title == "VIP" and (
                    self.bot.config.get_bot_config()
                    .get("bot_features")
                    .get("cogs")
                    .get("vip_cog")
                    .get("enable_vip_cog")
                ):
                    broadcaster: User = (
                        await self.fetch_users(ids=[event.channel_id])
                    )[0]
                    chatter: Chatter | PartialChatter = broadcaster.channel.get_chatter(
                        name=event.user.name
                    )
                    cog: VIP_Cog | Cog = self.bot.get_cog(name="VIP_Cog")
                    await cog.add_channel_vip(
                        broadcaster=broadcaster,
                        chatter=chatter,
                        event=event,
                    )

    async def start_pubsub(self):
        # Start listening to supported PubSub topics for channel points and bits
        await self.pubsub.subscribe_topics(self.topics)
        print(
            f"{Fore.RED}PubSubClient is now listening for events in {Fore.MAGENTA}{self.users_channel_id}"
            f"{Fore.RED}'s channel.{Style.RESET_ALL}"
        )


class CustomPubSubPool(pubsub.PubSubPool):
    async def auth_fail_hook(self, topics: List[pubsub.Topic]):
        """
        This function is a coroutine. This is a hook that can be overridden in a subclass. From this hook, you can
        refresh expired tokens (or prompt a user for new ones), and resubscribe to the events.
        The topics will not be automatically resubscribed to. You must do it yourself by calling subscribe_topics()
        with the topics after obtaining new tokens.

        Parameters:
        - topics (List[Topic]): The topics that have been de-authorized.
        Typically, these will all contain the same token.

        https://twitchio.dev/en/latest/exts/pubsub.html#twitchio.ext.pubsub.PubSubPool.auth_fail_hook
        """
        for topic in topics:
            topic.token = "new_token"  # TODO: Refresh self.users_oauth_token

        await self.subscribe_topics(topics)

    async def reconnect_hook(
        self, node: pubsub.PubSubWebsocket, topics: List[pubsub.Topic]
    ) -> List[pubsub.Topic]:
        """
        This is a low-level hook that can be overridden in a subclass. it is called whenever a node
        has to reconnect for any reason, from the twitch edge lagging out to being told to by twitch.
        This hook allows you to modify the topics, potentially updating tokens or removing topics altogether.

        Parameters:
        - node (PubSubWebsocket): The node that is reconnecting.
        - topics (List[Topic]): The topics that this node has.

        Returns:
        - List[Topic]: The list of topics this node should have.

        https://twitchio.dev/en/latest/exts/pubsub.html#twitchio.ext.pubsub.PubSubPool.reconnect_hook
        """
        # TODO: Modify topics if needed
        # You could update tokens or change topics based on your logic here

        # For example, let's say we want to add a new topic dynamically
        # topics.append(pubsub.subscriptions(self.user_id))  # Uncomment to add subscriptions

        # Return the modified list of topics
        return topics
