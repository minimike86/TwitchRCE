import asyncio
from typing import Optional
from colorama import Fore, Back, Style

import aiohttp
import json

import settings


class TwitchApiAuth:

    def __init__(self):
        self.loop = asyncio.get_event_loop()

    async def client_credentials_grant_flow(self):
        """
        The client credentials grant flow is meant only for server-to-server API requests that use an app access token.
        To get an access token, send an HTTP POST request to https://id.twitch.tv/oauth2/token. Set the following x-www-form-urlencoded parameters as appropriate for your app.

        Parameter	    Required?	Type	Description
        client_id	    Yes	        String	Your app’s registered client ID.
        client_secret	Yes	        String	Your app’s registered client secret.
        grant_type	    Yes	        String	Must be set to client_credentials.
        """
        url = "https://id.twitch.tv/oauth2/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        params = {
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
            "grant_type": "client_credentials"
        }
        request_body = {
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, params=params, headers=headers, data=json.dumps(request_body)) as resp:
                status = resp.status
                data = await resp.json()
        if status == 400:
            print(f"{Fore.RED}Failed to get app access token.{Style.RESET_ALL}")
            exit(0)
        if status == 200:
            print(f"{Fore.GREEN}Generated new app access token!{Style.RESET_ALL}")  # : {json.dumps(data)}.")
            return data

    async def obtain_access_token(self, code: str, redirect_uri: str):
        """
        https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#client-credentials-grant-flow
        To get the tokens, send an HTTP POST request to https://id.twitch.tv/oauth2/token. Set the following x-www-form-urlencoded parameters in the body of the POST.

        Parameter	    Required?	Type	Description
        client_id	    Yes	        String	Your app’s registered client ID.
        client_secret	Yes	        String	Your app’s registered client secret.
        code	        Yes	        String	The code that the /authorize response returned in the code query parameter.
        grant_type	    Yes	        String	Must be set to authorization_code.
        redirect_uri	Yes	        URI	    Your app’s registered redirect URI.
        """
        url = "https://id.twitch.tv/oauth2/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        params = {
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": f"{redirect_uri}"
        }
        request_body = {
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, params=params, headers=headers, data=json.dumps(request_body)) as resp:
                status = resp.status
                data = await resp.json()
        if status == 400:
            print(f"Failed to validate token using code: {code}.")
            exit(0)
        if status == 200:
            print(f"Token validated: {json.dumps(data)}.")
            return data

    async def refresh_access_token(self, refresh_token: str):
        """
        https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#client-credentials-grant-flow
        To get the tokens, send an HTTP POST request to https://id.twitch.tv/oauth2/token. Set the following x-www-form-urlencoded parameters in the body of the POST.

        Parameter	    Required?	Type	Description
        client_id	    Yes	        String	Your app’s registered client ID.
        client_secret	Yes	        String	Your app’s registered client secret.
        grant_type	    Yes	        String	Must be set to authorization_code.
        refresh_token	Yes	        String  The refresh token issued to the client.
        """
        url = "https://id.twitch.tv/oauth2/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        params = {
            "client_id": settings.CLIENT_ID,
            "client_secret": settings.CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": f"{refresh_token}"
        }
        request_body = {
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, params=params, headers=headers, data=json.dumps(request_body)) as resp:
                status = resp.status
                data = await resp.json()
        if status == 400:
            print(f"{Fore.RED}Failed to refresh token using token: {Fore.MAGENTA}{refresh_token}{Fore.RED}.{Style.RESET_ALL}")
            return data
        if status == 200:
            print(f"{Fore.GREEN}Token refreshed: {Fore.MAGENTA}{json.dumps(data)}{Fore.GREEN}.{Style.RESET_ALL}")
            return data

    async def validate_token(self, access_token: str) -> bool:
        """
        https://dev.twitch.tv/docs/authentication/validate-tokens/
        WARNING Twitch periodically conducts audits to discover applications that are not validating access tokens hourly as required.
        """
        url = "https://id.twitch.tv/oauth2/validate"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"OAuth {access_token}"
        }
        params = {
        }
        request_body = {
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params, headers=headers, data=json.dumps(request_body)) as resp:
                status = resp.status
                data = await resp.json()
        if status == 401:
            print(f"{Fore.RED}Invalid access token: {Fore.MAGENTA}{json.dumps(data)}{Fore.RED}.{Style.RESET_ALL}")
            return False
        if status == 200:
            print(f"{Fore.GREEN}Valid access token for user: {Fore.MAGENTA}{data.get('login')}{Fore.GREEN}.{Style.RESET_ALL}")
            return True

    async def get_users(self, access_token: str, ids=Optional[int], logins=Optional[str]):
        """
        https://dev.twitch.tv/docs/authentication/validate-tokens/
        WARNING Twitch periodically conducts audits to discover applications that are not validating access tokens hourly as required.
        """
        url = "https://api.twitch.tv/helix/users"
        headers = {
            "Client-Id": settings.CLIENT_ID,
            "Authorization": f"Bearer {access_token}"
        }
        params = {
        }
        request_body = {
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params, headers=headers, data=json.dumps(request_body)) as resp:
                status = resp.status
                data = await resp.json()
        if status == 401:
            """
            The Authorization header is required and must contain an app access token or user access token.
            The access token is not valid.
            The ID specified in the Client-Id header does not match the client ID specified in the access token.
            """
            print(f"Unauthorized: {json.dumps(data)}.")
        if status == 400:
            """
            The id or login query parameter is required unless the request uses a user access token.
            The request exceeded the maximum allowed number of id and/or login query parameters.
            """
            print(f"Bad Request: {json.dumps(data)}.")
        if status == 200:
            print(f"Successfully retrieved the specified users’ information: {json.dumps(data)}.")
            return data['data']
