import asyncio
import json

import settings
import aiohttp


class TwitchImplicitGrantFlow:

    def __init__(self):
        self.loop = asyncio.get_event_loop()

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
