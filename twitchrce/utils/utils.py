import logging

import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from colorama import Fore, Style
from moto.dynamodb.exceptions import ResourceNotFoundException

from twitchrce.config import bot_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class Utils:

    @staticmethod
    async def get_app_token() -> str:
        """Uses the bots' client id and secret to generate a new application token via client credentials grant flow"""
        from twitchrce.api.twitch.twitch_api_auth import TwitchApiAuth
        client_creds_grant_flow = await TwitchApiAuth().client_credentials_grant_flow()
        logger.info(
            f"{Fore.LIGHTWHITE_EX}Updated {Fore.LIGHTCYAN_EX}app access token{Fore.LIGHTWHITE_EX}!{Style.RESET_ALL}"
        )
        return client_creds_grant_flow["access_token"]

    @staticmethod
    async def refresh_user_token(user: any) -> str:
        # TODO: Replace with lambda calls
        from twitchrce.api.twitch.twitch_api_auth import TwitchApiAuth
        auth_result = await TwitchApiAuth().refresh_access_token(
            refresh_token=user.get("refresh_token")
        )
        try:
            config = bot_config.BotConfig()
            region_name = config.get_bot_config().get("aws").get("region_name")
            dynamodb = boto3.resource(
                "dynamodb", region_name=region_name
            )
            user_table = dynamodb.Table("MSecBot_User")
            user_table.update_item(
                Key={"id": user.get("id")},
                UpdateExpression="set access_token=:a, refresh_token=:r, expires_in=:e",
                ExpressionAttributeValues={
                    ":a": auth_result.get("access_token"),
                    ":r": auth_result.get("refresh_token"),
                    ":e": auth_result.get("expires_in"),
                },
                ReturnValues="UPDATED_NEW",
            )
            logger.info(
                f"{Fore.LIGHTWHITE_EX}Updated access_token and refresh_token for user {Fore.LIGHTCYAN_EX}{user['login']}"
                f"{Fore.LIGHTWHITE_EX}!{Style.RESET_ALL}"
            )
        except ResourceNotFoundException as resource_error:
            logger.error("ResourceNotFoundException", resource_error)
            raise resource_error
        except (NoCredentialsError, PartialCredentialsError) as credential_error:
            logger.error("Credentials Error", credential_error)
            raise credential_error
        return auth_result.get("access_token")

    async def check_valid_token(self, user: any) -> bool:
        # TODO: Replace with lambda calls
        """
        Asynchronously checks if a user's access token is valid. If the token is invalid,
        attempts to refresh the token and validates it again.

        Args:
            user (any): A user object or dictionary containing the user's access token
                under the key "access_token".

        Returns:
            bool: True if the user's access token is valid after validation or refresh;
                  False if it remains invalid.
        """
        from twitchrce.api.twitch.twitch_api_auth import TwitchApiAuth
        is_valid_token = await TwitchApiAuth().validate_token(
            access_token=user.get("access_token")
        )
        if not is_valid_token:
            access_token = await self.refresh_user_token(user=user)
            is_valid_token = await TwitchApiAuth().validate_token(access_token=access_token)
        return is_valid_token

    @staticmethod
    def redact_secret_string(secret_string: str, visible_chars: int = 4) -> str:
        """
        Redact a secret_string, showing only the first and last few characters.

        Parameters:
        - token (str): The token to redact.
        - visible_chars (int): The number of characters to show at the start and end.

        Returns:
        - str: The redacted secret_string, e.g., "abcd****wxyz".
        """
        if len(secret_string) <= visible_chars * 2:
            # If token is too short, fully redact it
            return "*" * len(secret_string)

        # Keep the first and last `visible_chars` characters, redact the rest
        return (
            f"{secret_string[:visible_chars]}"
            f"{'*' * (len(secret_string) - visible_chars * 2)}"
            f"{secret_string[-visible_chars:]}"
        )
