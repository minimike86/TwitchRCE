import logging

import twitchio
from custom_bot import CustomBot
from twitchio import Chatter, PartialChatter, PartialUser, User
from twitchio.ext import commands, pubsub

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class VIPCog(commands.Cog):

    def __init__(self, bot: CustomBot):
        self.bot = bot

    @commands.Cog.event()
    async def event_message(self, message: twitchio.Message):
        if message.echo:
            return
        print("VIPCog: ", message.author.name, message.content)

    async def add_channel_vip(
        self,
        broadcaster: User | PartialUser,
        chatter: Chatter | PartialChatter,
        event: pubsub.PubSubChannelPointsMessage,
    ):
        if chatter.is_mod:
            """Check if the redeemer is already a moderator and abort"""
            logger.info(f"{chatter.display_name} is already a MOD")
            await self.bot.update_reward_redemption_status(
                broadcaster=broadcaster,
                reward_id=event.id,
                custom_reward_id=event.reward.id,
                status=False,
            )
            await self.bot.post_chat_announcement(
                broadcaster=broadcaster,
                moderator=self.bot.bot_user,
                message=f"{chatter.display_name} is already a MOD your channel points have been refunded",
                color="orange",
            )

        elif chatter.is_vip:
            """Check if the redeemer is already a VIP and abort"""
            logger.info(f"{chatter.display_name} is already a VIP")
            await self.bot.update_reward_redemption_status(
                broadcaster=broadcaster,
                reward_id=event.id,
                custom_reward_id=event.reward.id,
                status=False,
            )
            await self.bot.post_chat_announcement(
                broadcaster=broadcaster,
                moderator=self.bot.bot_user,
                message=f"{chatter.display_name} is already a VIP your channel points have been refunded",
                color="orange",
            )

        else:
            """Add redeemer as a VIP, and auto-fulfill the redemption"""
            broadcaster_token = (
                "broadcaster_token"  # TODO: Get actual broadcaster_token from database
            )
            await broadcaster.add_channel_vip(
                token=broadcaster_token, user_id=int(chatter.id)
            )
            await self.bot.update_reward_redemption_status(
                broadcaster=broadcaster,
                reward_id=event.id,
                custom_reward_id=event.reward.id,
                status=True,
            )
            await self.bot.post_chat_announcement(
                broadcaster=broadcaster,
                moderator=self.bot.bot_user,
                message=f"Welcome {chatter.display_name} to the VIP family!",
                color="green",
            )
