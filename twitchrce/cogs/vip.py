import twitchio
from twitchio.ext import commands, pubsub

from twitchrce import custom_bot


class VIPCog(commands.Cog):

    def __init__(self, bot: custom_bot.Bot):
        self.bot = bot

    @commands.Cog.event()
    async def event_message(self, message: twitchio.Message):
        if message.echo:
            return
        print("VIPCog: ", message.author.name, message.content)

    async def add_channel_vip(
        self,
        channel_id: int,
        author_id: str,
        author_login: str,
        event: pubsub.PubSubChannelPointsMessage,
    ):
        broadcaster = await self.bot._http.get_users(ids=[channel_id], logins=[])
        broadcaster_access_token_resultset = self.bot.database.fetch_user_access_token(
            broadcaster_id=broadcaster[0]["id"]
        )
        broadcaster_access_token: str = broadcaster_access_token_resultset[
            "access_token"
        ]
        mod_access_token_resultset = self.bot.database.fetch_user_access_token(
            broadcaster_id=self.bot.user_id
        )
        mod_access_token: str = mod_access_token_resultset["access_token"]

        # Get list of channel mods
        mods = await self.bot._http.get_channel_moderators(
            token=broadcaster_access_token, broadcaster_id=str(broadcaster[0]["id"])
        )
        mods_user_ids = [str(mod["user_id"]) for mod in mods]

        # Get list of channel vips
        vips = await self.bot._http.get_channel_vips(
            token=broadcaster_access_token, broadcaster_id=str(broadcaster[0]["id"])
        )
        vips_user_ids = [str(vip["user_id"]) for vip in vips]

        if author_id in mods_user_ids:
            """Check if the redeemer is already a moderator and abort"""
            print(f"{author_login} is already a MOD")
            await self.bot._http.update_reward_redemption_status(
                token=broadcaster_access_token,
                broadcaster_id=str(broadcaster[0]["id"]),
                reward_id=event.id,
                custom_reward_id=event.reward.id,
                status=False,
            )
            await self.bot._http.post_chat_announcement(
                token=mod_access_token,
                broadcaster_id=str(broadcaster[0]["id"]),
                moderator_id=self.bot.user_id,
                message=f"{author_login} is already a MOD; your channel points have been refunded",
                color="orange",
            )
        elif author_id in vips_user_ids:
            """Check if the redeemer is already a VIP and abort"""
            print(f"{author_login} is already a VIP")
            await self.bot._http.update_reward_redemption_status(
                token=broadcaster_access_token,
                broadcaster_id=str(broadcaster[0]["id"]),
                reward_id=event.id,
                custom_reward_id=event.reward.id,
                status=False,
            )
            await self.bot._http.post_chat_announcement(
                token=mod_access_token,
                broadcaster_id=str(broadcaster[0]["id"]),
                moderator_id=self.bot.user_id,
                message=f"{author_login} is already a VIP; your channel points have been refunded",
                color="orange",
            )

        else:
            """Add redeemer as a VIP, and auto-fulfill the redemption"""
            await self.bot._http.post_channel_vip(
                token=broadcaster_access_token,
                broadcaster_id=str(broadcaster[0]["id"]),
                user_id=author_id,
            )
            await self.bot._http.update_reward_redemption_status(
                token=broadcaster_access_token,
                broadcaster_id=str(broadcaster[0]["id"]),
                reward_id=event.id,
                custom_reward_id=event.reward.id,
                status=True,
            )
            await self.bot._http.post_chat_announcement(
                token=mod_access_token,
                broadcaster_id=str(broadcaster[0]["id"]),
                moderator_id=self.bot.user_id,
                message=f"Welcome {author_login} to the VIP family!",
                color="green",
            )
