from decouple import config


class BotConfig:
    def __init__(self):
        # Twitch Developer Credentials
        self.CLIENT_ID = config("CLIENT_ID")
        self.CLIENT_SECRET = config("CLIENT_SECRET")

        # Twitch Bot User Credentials
        self.BOT_USER_ID = config("BOT_USER_ID")
        self.BOT_OAUTH_TOKEN = config("BOT_OAUTH_TOKEN")

        # Virus Total Developer API Key
        self.VIRUS_TOTAL_API_KEY = config("VIRUS_TOTAL_API_KEY")

        # AWS Credentials
        self.REGION_NAME = config("REGION_NAME", default="eu-west-2")
        self.AWS_REGION = config("AWS_REGION", default="eu-west-2")
        self.AWS_DEFAULT_REGION = config("AWS_DEFAULT_REGION", default="eu-west-2")
        self.API_GATEWAY_INVOKE_URL = config("API_GATEWAY_INVOKE_URL")
        self.API_GATEWAY_ROUTE = config(
            "API_GATEWAY_ROUTE", default="/twitch/oauth2/authorization_code"
        )

        # Additional Twitch Bot Variables
        self.BOT_INITIAL_CHANNELS = [{"id": 125444292, "login": "msec"}]
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
                "app_auth": {
                    "client_id": self.CLIENT_ID,
                    "client_secret": self.CLIENT_SECRET,
                },
                "bot_auth": {
                    "bot_user_id": self.BOT_USER_ID,
                    "bot_oauth_token": self.BOT_OAUTH_TOKEN,
                },
                "bot_initial_channels": self.BOT_INITIAL_CHANNELS,
            },
            "bot_features": {
                "enable_commands": False,
                "enable_psclient": False,
                "enable_esclient": False,
                "cogs": {
                    "rce_cog": {
                        "enable_rce_cog": False,
                        "cmd_allow_list": self.CMD_ALLOW_LIST,
                    },
                    "vip_cog": {
                        "enable_vip_cog": False,
                    },
                },
                "virus_total": {
                    "enable_virus_total": False,
                    "virus_total_api_key": self.VIRUS_TOTAL_API_KEY,
                },
            },
            "aws": {
                "aws_region": self.AWS_REGION,
                "aws_default_region": self.AWS_DEFAULT_REGION,
                "region_name": self.REGION_NAME,
                "api_gateway": {
                    "api_gateway_invoke_url": self.API_GATEWAY_INVOKE_URL,
                    "api_gateway_route": self.API_GATEWAY_ROUTE,
                },
            },
        }
