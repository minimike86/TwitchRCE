import socketserver
from http.server import SimpleHTTPRequestHandler
from typing import Callable, Any


class CodeHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if "/auth" in self.path:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
        elif "code" in self.path:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

    def log_request(self, code='-', size='-'):
        self.log_message('"%s" %s %s', self.requestline, str(code), str(size))
        # Stop the server if we get USER_IMPLICIT_GRANT_FLOW code back
        if "code" in self.path:
            self.server.code = str(self.path.split("=")[1]).replace('&scope', '')
            print("USER_IMPLICIT_GRANT_FLOW_CODE: done")
            self.server.stop = True


class ThreadingTCPServerWithStop(socketserver.ThreadingTCPServer):
    def __init__(
            self: Any,
            server_address: tuple[str, int],
            RequestHandlerClass: Callable[[Any, Any, Any], socketserver.BaseRequestHandler],
            bind_and_activate: bool = ...
    ):
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        self.stop = None
        self.code = None

    def server_bind(self):
        self.stop = False
        self.code = ""
        super().server_bind()

    def serve_forever(self, poll_interval=1):
        while not self.stop:
            self.handle_request()

# TODO: if tokens are missing use this code to obtain new tokens
# # Get UserID via Authorization code grant flow
# # https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#authorization-code-grant-flow
# scope = "analytics:read:extensions analytics:read:games bits:read channel:edit:commercial channel:manage:broadcast channel:read:charity channel:manage:extensions channel:manage:moderators channel:manage:polls channel:manage:predictions channel:manage:raids channel:manage:redemptions channel:manage:schedule channel:manage:videos channel:read:editors channel:read:goals channel:read:hype_train channel:read:polls channel:read:predictions channel:read:redemptions channel:read:stream_key channel:read:subscriptions channel:read:vips channel:manage:vips clips:edit moderation:read moderator:manage:announcements moderator:manage:automod moderator:read:automod_settings moderator:manage:automod_settings moderator:manage:banned_users moderator:read:blocked_terms moderator:manage:blocked_terms moderator:manage:chat_messages moderator:read:chat_settings moderator:manage:chat_settings moderator:read:chatters moderator:read:followers moderator:read:shield_mode moderator:manage:shield_mode moderator:read:shoutouts moderator:manage:shoutouts user:edit user:edit:follows user:manage:blocked_users user:read:blocked_users user:read:broadcast user:manage:chat_color user:read:email user:read:follows user:read:subscriptions user:manage:whispers channel:moderate chat:edit chat:read whispers:read whispers:edit"
# authorization_url = f"https://id.twitch.tv/oauth2/authorize?client_id={settings.CLIENT_ID}" \
#                     f"&force_verify=true" \
#                     f"&redirect_uri=http://localhost:3000/auth" \
#                     f"&response_type=code" \
#                     f"&scope={scope.replace(' ', '%20')}" \
#                     f"&state={secrets.token_hex(16)}"
# print("Launching auth site:", authorization_url)
#
# logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
# with ThreadingTCPServerWithStop(("0.0.0.0", 3000), CodeHandler) as tcpserver:
#     logger.info(f"Serving on {tcpserver.server_address}...")
#     tcpserver.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     if tcpserver.stop is not True:
#         tcpserver.stop = False
#         tcpserver.serve_forever(poll_interval=0.1)
#     logger.info('Server stopped')
#
# twitch_api_auth = TwitchApiAuth()
# auth_result = await twitch_api_auth.obtain_access_token(code=tcpserver.code,
#                                                         redirect_uri='http://localhost:3000/auth')
# http_client.token = auth_result['access_token']
# users = await http_client.get_users(ids=[], logins=[], token=auth_result['access_token'])
# db.insert_user_data(broadcaster_id=users[0]['id'], broadcaster_login=users[0]['login'],
#                     email=users[0]['email'], access_token=auth_result['access_token'],
#                     expires_in=auth_result['expires_in'], refresh_token=auth_result['refresh_token'],
#                     scope=auth_result['scope'])
