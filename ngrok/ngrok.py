from pyngrok import ngrok

import settings


class NgrokClient:
    _tunnels: ngrok = None
    _auth_tunnel: ngrok = None
    _eventsub_tunnel: ngrok = None

    def __init__(self, loop):
        if self._tunnels is None:
            try:
                self._loop = loop
                self._auth_tunnel = ngrok.connect(name='auth', bind_tls=True)
                self._eventsub_tunnel = ngrok.connect(name='eventsub', bind_tls=True)
                self._tunnels = ngrok.get_tunnels()

            except BaseException as e:
                print("Failed to instantiate ngrok http_tunnel: ", e)
                exit(0)

    async def start(self) -> (str, str):
        self._tunnels = ngrok.get_tunnels()
        if len(self._tunnels) < 1:
            self._tunnels = self._loop.run_until_complete(await self.get_ngrok_tunnels_public_urls())
        return await self.get_ngrok_tunnels_public_urls()

    async def get_auth_tunnel(self) -> str:
        return self._auth_tunnel.public_url

    async def get_eventsub_tunnel(self) -> str:
        return self._eventsub_tunnel.public_url

    async def get_ngrok_tunnels(self) -> ngrok:
        return self._tunnels

    async def get_ngrok_tunnels_public_urls(self) -> (str, str):
        auth_public_url = await self.get_auth_tunnel()
        eventsub_public_url = await self.get_eventsub_tunnel()

        for tunnel in await self.get_ngrok_tunnels():
            # print(f"{tunnel.name}: {tunnel.public_url}")

            if str(settings.AUTH_URI_PORT) in tunnel.config['addr']:
                auth_public_url = f"{tunnel.public_url}/auth"
                print(f"auth_public_url: {auth_public_url} -> {tunnel.config['addr']}")

            if str(settings.EVENTSUB_URI_PORT) in tunnel.config['addr']:
                eventsub_public_url = f"{tunnel.public_url}/eventsub"
                print(f"eventsub_public_url: {eventsub_public_url} -> {tunnel.config['addr']}")

        return auth_public_url, eventsub_public_url
