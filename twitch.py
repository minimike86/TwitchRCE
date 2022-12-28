import json
import traceback

from twitchio.ext import pubsub

import settings
import aiohttp


class Twitch:

    def __init__(self, broadcaster_id: str):
        self.broadcaster_id = broadcaster_id

    async def get_custom_rewards(self):
        url = "https://api.twitch.tv/helix/channel_points/custom_rewards"
        params = {
            "broadcaster_id": self.broadcaster_id
        }
        headers = {
            "client-id": settings.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {settings.ACCESS_TOKEN}"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params, headers=headers) as resp:
                data = await resp.json()
        if not data:
            print("Failed to get redemptions.")
        else:
            print("Got redemptions.")
            return data.get("data")

    async def create_custom_reward(self, title: str, cost: int,
                                   is_global_cooldown_enabled: bool = False, global_cooldown_seconds: int = 1):
        url = "https://api.twitch.tv/helix/channel_points/custom_rewards"
        params = {
            "broadcaster_id": self.broadcaster_id
        }
        headers = {
            "client-id": settings.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {settings.ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        request_body = {
            "title": title,
            "cost": cost,
            "is_global_cooldown_enabled": is_global_cooldown_enabled,
            "global_cooldown_seconds": global_cooldown_seconds
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, params=params, headers=headers, data=json.dumps(request_body)) as resp:
                data = await resp.json()
                stream = data.get("data")
        if not stream:
            print("Failed to create redemption.")
        else:
            print("Created redemption.")

    async def update_redemption_status(self, reward_ids: str, reward_id: str, status: bool):
        """
        :param reward_ids: A list of IDs that identify the redemptions to update. To specify more than one ID, include this
                    parameter for each redemption you want to update. For example, id=1234&id=5678. You may specify a
                    maximum of 50 IDs.
        :param reward_id: The ID that identifies the reward that’s been redeemed.
        :param status: True = FULFILLED, False = CANCELED
        Documentation: https://dev.twitch.tv/docs/api/reference#update-redemption-status
        """
        url = "https://api.twitch.tv/helix/channel_points/custom_rewards/redemptions"
        params = {
            "id": reward_ids,
            "broadcaster_id": self.broadcaster_id,
            "reward_id": reward_id
        }
        headers = {
            "client-id": settings.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {settings.ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        if status:
            request_body = {
                "status": "FULFILLED"
            }
        else:
            request_body = {
                "status": "CANCELED"
            }
        async with aiohttp.ClientSession() as session:
            async with session.patch(url=url, params=params, headers=headers, data=json.dumps(request_body)) as resp:
                data = await resp.json()
                stream = data.get("data")
        if not stream:
            print("Failed to update redemption status.")
        else:
            if status:
                print("Updated redemption status to FULFILLED")
            else:
                print("Updated redemption status to CANCELED")

    async def delete_custom_reward(self, reward_id: str):
        url = "https://api.twitch.tv/helix/channel_points/custom_rewards"
        params = {
            "broadcaster_id": self.broadcaster_id,
            "id": reward_id
        }
        headers = {
            "client-id": settings.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {settings.ACCESS_TOKEN}"
        }
        async with aiohttp.ClientSession() as session:
            async with session.delete(url=url, params=params, headers=headers) as resp:
                data = resp.status
        if not data == 204:
            print("Failed to delete redemption.")
        else:
            print("Deleted redemption.")

    async def send_chat_announcement(self, message: str, color: str):
        url = "https://api.twitch.tv/helix/chat/announcements"
        params = {
            "broadcaster_id": self.broadcaster_id,
            "moderator_id": self.broadcaster_id
        }
        headers = {
            "client-id": settings.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {settings.ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        request_body = {
            "message": message,
            "color": color
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url=url, params=params, headers=headers, data=json.dumps(request_body)) as resp:
                    data = resp.status
            if not data == 204:
                print("Failed to create announcement.")
            else:
                print("Announcement made.")
        except Exception as err:
            print(f"something broke {type(err)}", traceback.format_exc())

    async def get_vips(self, broadcaster_id: str):
        url = "https://api.twitch.tv/helix/channels/vips"
        params = {
            "broadcaster_id": broadcaster_id
        }
        headers = {
            "client-id": settings.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {settings.ACCESS_TOKEN}"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params, headers=headers) as resp:
                status = resp.status
                data = await resp.json()
                if status == 204:
                    print("Failed to get VIPS.")
                elif status == 200:
                    # print(f"get_vips: {data}")
                    return data.get('data')

    async def add_channel_vip(self, event: pubsub.PubSubChannelPointsMessage, broadcaster_id: str):
        url = "https://api.twitch.tv/helix/channels/vips"
        params = {
            "user_id": event.user.id,
            "broadcaster_id": broadcaster_id
        }
        headers = {
            "client-id": settings.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {settings.ACCESS_TOKEN}"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, params=params, headers=headers) as resp:
                status = resp.status
                if status == 409:
                    print("The broadcaster doesnt have available VIP slots.")
                    await Twitch(settings.BROADCASTER_ID) \
                        .update_redemption_status(event.id, event.reward.id, False)
                elif status == 404:
                    print("The ID in broadcaster_id was not found. / The ID in user_id was not found.")
                    await Twitch(settings.BROADCASTER_ID) \
                        .update_redemption_status(event.id, event.reward.id, False)
                elif status == 422:
                    print("The user in the user_id query parameter is already a VIP.")
                    await Twitch(settings.BROADCASTER_ID) \
                        .update_redemption_status(event.id, event.reward.id, False)
                elif status == 204:
                    print("Successfully added the VIP.")
                    await Twitch(settings.BROADCASTER_ID) \
                        .update_redemption_status(event.id, event.reward.id, True)

    async def remove_channel_vip(self, user_id: str, broadcaster_id: str):
        pass

    async def get_moderators(self, broadcaster_id: str):
        url = "https://api.twitch.tv/helix/moderation/moderators"
        params = {
            "broadcaster_id": broadcaster_id
        }
        headers = {
            "client-id": settings.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {settings.ACCESS_TOKEN}"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params, headers=headers) as resp:
                status = resp.status
                data = await resp.json()
                if status == 400:
                    print("The broadcaster_id query parameter is required.")
                elif status == 401:
                    print("The access token is not valid.")
                elif status == 200:
                    # print(f"get_vips: {data}")
                    return data.get('data')
