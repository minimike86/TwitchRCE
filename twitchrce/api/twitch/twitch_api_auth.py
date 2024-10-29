import asyncio
import json
import logging
from typing import Optional

import aiohttp
from colorama import Fore, Style

from twitchrce.config import bot_config
from twitchrce.utils.utils import Utils

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class TwitchApiAuth:

    def __init__(self):
        self.config = bot_config.BotConfig().get_bot_config()
        self.loop = asyncio.get_event_loop()

    async def client_credentials_grant_flow(self) -> dict:
        """
        The client credentials grant flow is meant only for server-to-server API requests that use an app access token.
        To get an access token, send an HTTP POST request to https://id.twitch.tv/oauth2/token.
        Set the following x-www-form-urlencoded parameters as appropriate for your app.

        Parameter	    Required?	Type	Description
        client_id	    Yes	        String	Your app’s registered client ID.
        client_secret	Yes	        String	Your app’s registered client secret.
        grant_type	    Yes	        String	Must be set to client_credentials.
        """
        url = "https://id.twitch.tv/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        params = {
            "client_id": self.config.get("twitch").get("app_auth").get("client_id"),
            "client_secret": self.config.get("twitch")
            .get("app_auth")
            .get("client_secret"),
            "grant_type": "client_credentials",
        }
        request_body = {}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=url, params=params, headers=headers, data=json.dumps(request_body)
            ) as resp:
                status = resp.status
                data = await resp.json()
        if status == 400:
            logger.error(f"{Fore.RED}Failed to get app access token.{Style.RESET_ALL}")
            raise ValueError("Authentication failed: No credentials provided.")
        if status == 200:
            logger.info(
                f"{Fore.LIGHTWHITE_EX}Generated new {Fore.LIGHTCYAN_EX}app access token"
                f"{Fore.LIGHTWHITE_EX}!{Style.RESET_ALL}"
            )  # : {json.dumps(data)}.")
            return data

    async def obtain_access_token(self, code: str, redirect_uri: str) -> dict:
        """
        https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#client-credentials-grant-flow
        To get the tokens, send an HTTP POST request to https://id.twitch.tv/oauth2/token.
        Set the following x-www-form-urlencoded parameters in the body of the POST.

        Parameter	    Required?	Type	Description
        client_id	    Yes	        String	Your app’s registered client ID.
        client_secret	Yes	        String	Your app’s registered client secret.
        code	        Yes	        String	The code that the /authorize response returned to the code query parameter.
        grant_type	    Yes	        String	Must be set to authorization_code.
        redirect_uri	Yes	        URI	    Your app’s registered redirect URI.
        """
        url = "https://id.twitch.tv/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        params = {
            "client_id": self.config.get("twitch").get("app_auth").get("client_id"),
            "client_secret": self.config.get("twitch")
            .get("app_auth")
            .get("client_secret"),
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": f"{redirect_uri}",
        }
        request_body = {}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=url, params=params, headers=headers, data=json.dumps(request_body)
            ) as resp:
                status = resp.status
                data = await resp.json()
        if status == 400:
            logger.error(f"Failed to validate token using code: {code}.")
            raise ValueError("Authentication failed: No credentials provided.")
        if status == 200:
            logger.info(f"Token validated: {json.dumps(data)}.")
            return data

    async def refresh_access_token(self, refresh_token: str):
        """
        https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#client-credentials-grant-flow
        To get the tokens, send an HTTP POST request to https://id.twitch.tv/oauth2/token.
        Set the following x-www-form-urlencoded parameters in the body of the POST.

        Parameter	    Required?	Type	Description
        client_id	    Yes	        String	Your app’s registered client ID.
        client_secret	Yes	        String	Your app’s registered client secret.
        grant_type	    Yes	        String	Must be set to authorization_code.
        refresh_token	Yes	        String  The refresh token issued to the client.
        """
        url = "https://id.twitch.tv/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        params = {
            "client_id": self.config.get("twitch").get("app_auth").get("client_id"),
            "client_secret": self.config.get("twitch")
            .get("app_auth")
            .get("client_secret"),
            "grant_type": "refresh_token",
            "refresh_token": f"{refresh_token}",
        }
        request_body = {}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=url, params=params, headers=headers, data=json.dumps(request_body)
            ) as resp:
                status = resp.status
                data = await resp.json()
        if status == 400:
            from twitchrce.utils.utils import Utils

            logger.error(
                f"{Fore.RED}Refresh of user oauth access_token using refresh_token [{Fore.MAGENTA}"
                f"{Utils.redact_secret_string(refresh_token)}{Fore.RED}] has FAILED!.{Style.RESET_ALL}"
            )
            return data
        if status == 200:
            return data

    @staticmethod
    async def validate_token(access_token: str) -> bool:
        """
        https://dev.twitch.tv/docs/authentication/validate-tokens/
        WARNING Twitch periodically conducts audits to discover applications that are not validating access tokens
        hourly as required.
        """
        url = "https://id.twitch.tv/oauth2/validate"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"OAuth {access_token}",
        }
        params = {}
        request_body = {}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=url, params=params, headers=headers, data=json.dumps(request_body)
            ) as resp:
                status = resp.status
                data = await resp.json()
        if status == 401:
            logger.error(
                f"{Fore.LIGHTWHITE_EX}Access token [{Fore.MAGENTA}OAuth {Utils.redact_secret_string(access_token)}"
                f"{Fore.LIGHTWHITE_EX}] is {Fore.RED}INVALID{Fore.LIGHTWHITE_EX} - {Fore.YELLOW}{json.dumps(data)}"
                f"{Fore.LIGHTWHITE_EX}.{Style.RESET_ALL}"
            )
            return False
        if status == 200:
            logger.info(
                f"{Fore.LIGHTWHITE_EX}Access token [{Fore.MAGENTA}OAuth {Utils.redact_secret_string(access_token)}"
                f"{Fore.LIGHTWHITE_EX}] for user {Fore.LIGHTCYAN_EX}{data.get('login')}{Fore.LIGHTWHITE_EX} is "
                f"{Fore.GREEN}VALID{Fore.LIGHTWHITE_EX}!{Style.RESET_ALL}"
            )
            return True

    async def get_users(
        self, access_token: str, ids=Optional[int], logins=Optional[str]
    ):
        """
        https://dev.twitch.tv/docs/authentication/validate-tokens/
        WARNING Twitch periodically conducts audits to discover applications that are not validating access tokens hourly as required.
        """
        url = "https://api.twitch.tv/helix/users"
        headers = {
            "Client-Id": self.config.get("twitch").get("app_auth").get("client_id"),
            "Authorization": f"Bearer {access_token}",
        }
        params = {}
        request_body = {}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=url, params=params, headers=headers, data=json.dumps(request_body)
            ) as resp:
                status = resp.status
                data = await resp.json()
        if status == 401:
            """
            The Authorization header is required and must contain an app access token or user access token.
            The access token is not valid.
            The ID specified in the Client-Id header does not match the client ID specified in the access token.
            """
            logger.error(f"Unauthorized: {json.dumps(data)}.")
            raise ValueError(f"Authentication failed: {json.dumps(data)}.")
        if status == 400:
            """
            The id or login query parameter is required unless the request uses a user access token.
            The request exceeded the maximum allowed number of id and/or login query parameters.
            """
            logger.error(f"Bad Request: {json.dumps(data)}.")
            raise ValueError(f"Bad Request: {json.dumps(data)}.")
        if status == 200:
            logger.info(
                f"Successfully retrieved the specified users’ information: {json.dumps(data)}."
            )
            return data["data"]
