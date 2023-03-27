import asyncio
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
            print(f"Failed to get app access token.")
            exit(0)
        if status == 200:
            print(f"Generated app access token: {json.dumps(data)}.")
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
            print(f"Failed to refresh token using token: {refresh_token}.")
            exit(0)
        if status == 200:
            print(f"Token refreshed: {json.dumps(data)}.")
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
            print(f"Invalid access token: {json.dumps(data)}.")
            return False
        if status == 200:
            print(f"Valid access token: {json.dumps(data)}.")
            return True
