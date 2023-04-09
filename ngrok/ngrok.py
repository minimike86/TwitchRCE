from pyngrok import ngrok, conf
from colorama import Fore, Back, Style

import settings


class NgrokClient:
    _tunnels: ngrok = None
    _auth_tunnel: ngrok = None
    _eventsub_tunnel: ngrok = None

    def __init__(self, loop):
        if self._tunnels is None:

            conf.get_default().config_path = '/home/kali/.ngrok2/ngrok.yml'
            conf.get_default().ngrok_path = '/usr/local/bin/ngrok'
            conf.get_default().ngrok_version = 'v3'
            conf.get_default().startup_timeout = 30
            pyngrok_config = conf.get_default()

            try:
                self._loop = loop
                self._tunnels = ngrok.get_tunnels()
                if len(self._tunnels) == 0:
                    self._auth_tunnel = ngrok.connect(name='auth', pyngrok_config=pyngrok_config, bind_tls=True)
                    self._eventsub_tunnel = ngrok.connect(name='eventsub', pyngrok_config=pyngrok_config, bind_tls=True)
                    self._tunnels = ngrok.get_tunnels()

            except BaseException as error:
                print(f"{Fore.RED}Failed to instantiate ngrok http_tunnel: {error}{Style.RESET_ALL}")
                # exit(0)

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
                print(f"{Fore.RED}auth_public_url: {Fore.MAGENTA}{auth_public_url}{Fore.RED} -> {Fore.MAGENTA}{tunnel.config['addr']}{Fore.RED}.{Style.RESET_ALL}")

            if str(settings.EVENTSUB_URI_PORT) in tunnel.config['addr']:
                eventsub_public_url = f"{tunnel.public_url}/eventsub"
                print(f"{Fore.RED}eventsub_public_url: {Fore.MAGENTA}{eventsub_public_url}{Fore.RED} -> {Fore.MAGENTA}{tunnel.config['addr']}{Fore.RED}.{Style.RESET_ALL}")

        return auth_public_url, eventsub_public_url
