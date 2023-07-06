import asyncio
import logging
import secrets
import socketserver
from colorama import Fore, Style
from http.server import SimpleHTTPRequestHandler
from typing import Callable, Any

import settings
from api.twitch.twitch_api_auth import TwitchApiAuth
from db.database import Database

# init asyncio
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

scope = "analytics:read:extensions analytics:read:games bits:read channel:edit:commercial " \
        "channel:manage:broadcast channel:read:charity channel:manage:extensions channel:manage:moderators " \
        "channel:manage:polls channel:manage:predictions channel:manage:raids channel:manage:redemptions " \
        "channel:manage:schedule channel:manage:videos channel:read:editors channel:read:goals " \
        "channel:read:hype_train channel:read:polls channel:read:predictions channel:read:redemptions " \
        "channel:read:stream_key channel:read:subscriptions channel:read:vips channel:manage:vips " \
        "clips:edit moderation:read moderator:manage:announcements moderator:manage:automod " \
        "moderator:read:automod_settings moderator:manage:automod_settings moderator:manage:banned_users " \
        "moderator:read:blocked_terms moderator:manage:blocked_terms moderator:manage:chat_messages " \
        "moderator:read:chat_settings moderator:manage:chat_settings moderator:read:chatters " \
        "moderator:read:followers moderator:read:shield_mode moderator:manage:shield_mode " \
        "moderator:read:shoutouts moderator:manage:shoutouts user:edit user:edit:follows " \
        "user:manage:blocked_users user:read:blocked_users user:read:broadcast user:manage:chat_color " \
        "user:read:email user:read:follows user:read:subscriptions user:manage:whispers channel:moderate " \
        "chat:edit chat:read whispers:read whispers:edit"


class CodeHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        if "/auth" in self.path:
            self.send_response(code=200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            if "code" in self.path:
                # Write the HTML content to the response body
                html = f"<html><body>Success! :)</body></html>"
                self.wfile.write(bytes(html, "utf8"))

            else:
                # Write the HTML content to the response body
                html = f"<html><body><button style=\"background-color: #9146ff; color: #ffffff; font-weight: bold; " \
                       f"padding: 8px;\" onclick=\"window.location.href='{self.server.authorization_url}'\">" \
                       f"Authenticate with Twitch</button></body></html>"
                self.wfile.write(bytes(html, "utf8"))

        else:
            self.send_response(code=200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

    def log_request(self, code='-', size='-'):
        self.log_message('"%s" %s %s', self.requestline, str(code), str(size))
        if "code" in self.path:
            self.server.code = str(self.path.split("=")[1]).replace('&scope', '')
            loop.run_until_complete(self.use_code_and_store_access_token(code=self.server.code,
                                                                         redirect_uri=self.server.redirect_uri))
            self.server.stop = True

    async def use_code_and_store_access_token(self, code: str, redirect_uri: str):
        twitch_api_auth = TwitchApiAuth()
        auth_result = await twitch_api_auth.obtain_access_token(code=code, redirect_uri=redirect_uri)
        users = await twitch_api_auth.get_users(access_token=auth_result['access_token'], ids=[], logins=[])

        # init db
        db = Database()
        try:
            db.insert_user_data(broadcaster_id=users[0]['id'], broadcaster_login=users[0]['login'],
                                email=users[0]['email'], access_token=auth_result['access_token'],
                                expires_in=auth_result['expires_in'], refresh_token=auth_result['refresh_token'],
                                scope=auth_result['scope'])
            print(f"database updated: login={users[0]['login']}, login={users[0]['id']}, "
                  f"access_token={auth_result['access_token']}, refresh_token={auth_result['refresh_token']}")
        except Exception as error:
            print(error)


class ThreadingTCPServerWithStop(socketserver.ThreadingTCPServer):
    def __init__(
            self: Any,
            server_address: tuple[str, int],
            RequestHandlerClass: Callable[[Any, Any, Any], socketserver.BaseRequestHandler],
            bind_and_activate: bool = ...,
            redirect_uri: str = 'http://localhost:3000/auth'
    ):
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.redirect_uri = redirect_uri
        self.stop = None
        self.code = None

    def server_bind(self):
        self.stop = False
        self.code = ""
        super().server_bind()

    def serve_forever(self, poll_interval=1):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        authorization_url = f"https://id.twitch.tv/oauth2/authorize?client_id={settings.CLIENT_ID}" \
                            f"&force_verify=true" \
                            f"&redirect_uri={self.redirect_uri}" \
                            f"&response_type=code" \
                            f"&scope={scope.replace(' ', '%20')}" \
                            f"&state={secrets.token_hex(16)}"

        print(f"{Fore.RED}Launching auth site: {Fore.MAGENTA}{authorization_url}{Fore.RED}.{Style.RESET_ALL}")

        while not self.stop:
            self.handle_request()
