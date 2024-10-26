from decouple import config


class BotConfig:

    def __init__(self):
        self.CLIENT_ID = config("CLIENT_ID")
        self.CLIENT_SECRET = config("CLIENT_SECRET")
        self.VIRUS_TOTAL_API_KEY = config("VIRUS_TOTAL_API_KEY")
        self.BOT_USER_ID = config("BOT_USER_ID")
        self.BOT_JOIN_CHANNEL_ID = config("BOT_JOIN_CHANNEL_ID")
        self.BOT_JOIN_CHANNEL = config("BOT_JOIN_CHANNEL")
        self.MAX_VIP_SLOTS = config("MAX_VIP_SLOTS", default=10)
        self.CMD_ALLOW_LIST = [
            "aux",
            "cat",
            "echo",
            "grep",
            "id",
            "ifconfig",
            "ls",
            "netstat",
            "nslookup",
            "ping",
            "pwd",
            "which",
            "who",
            "whoami",
        ]

    def get_bot_config(self) -> dict:
        return {
            "twitch": {
                "client_id": self.CLIENT_ID,
                "client_secret": self.CLIENT_SECRET,
                "bot_user_id": self.BOT_USER_ID,
                "channel": {
                    "bot_join_channel_id": self.BOT_JOIN_CHANNEL_ID,
                    "bot_join_channel": self.BOT_JOIN_CHANNEL,
                    "max_vip_slots": self.MAX_VIP_SLOTS,
                },
            },
            "virus_total": {"virus_total_api_key": self.VIRUS_TOTAL_API_KEY},
            "rce_cog": {"cmd_allow_list": self.CMD_ALLOW_LIST},
        }
