from pyngrok import ngrok


class NgrokClient:

    _tunnels: ngrok = None
    _auth_tunnel: ngrok = None
    _eventsub_tunnel: ngrok = None

    def __init__(self):
        if self._tunnels is None:
            try:
                self._auth_tunnel = ngrok.connect(name='auth', bind_tls=True)
                self._eventsub_tunnel = ngrok.connect(name='eventsub', bind_tls=True)
                self._tunnels = ngrok.get_tunnels()

            except BaseException as e:
                print("Failed to instantiate ngrok http_tunnel: ", e)
                exit(0)

    def get_auth_tunnel(self) -> str:
        return self._auth_tunnel.public_url

    def get_eventsub_tunnel(self) -> str:
        return self._eventsub_tunnel.public_url

    def get_ngrok_tunnels(self) -> ngrok:
        return self._tunnels
