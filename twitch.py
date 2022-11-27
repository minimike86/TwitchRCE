import json
import traceback

import settings
import aiohttp


class Twitch:

    def __init__(self, broadcaster_id: str):
        self.broadcaster_id = broadcaster_id

    async def get_custom_reward(self):
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
                stream = list(filter(lambda reward: reward["title"] == "Kill My Shell", data.get("data")))
        if not stream:
            print("Failed to get redemptions.")
        else:
            print("Got redemptions.")
            return stream[0].get("id")

    async def create_custom_reward(self, title: str, cost: int,
                                   is_global_cooldown_enabled: bool, global_cooldown_seconds: int):
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
