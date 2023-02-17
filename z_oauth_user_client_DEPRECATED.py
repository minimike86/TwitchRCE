"""
# ====================================================================================
# auth grant for code
# ====================================================================================
"""
if settings.USER_IMPLICIT_GRANT_FLOW_CODE == '':

    # Get UserID via Authorization code grant flow
    # https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#authorization-code-grant-flow
    def redirect_to_authorization():
        scope = settings.CHAT_OAUTH_SCOPE
        authorization_url = f"https://id.twitch.tv/oauth2/authorize?client_id={settings.CLIENT_ID}" \
                            f"&force_verify=true" \
                            f"&redirect_uri=http://localhost:3000/auth" \
                            f"&response_type=code" \
                            f"&scope={scope}" \
                            f"&state={'crsf'}"
        print("Launching auth site:", authorization_url)
    redirect_to_authorization()

"""
# ====================================================================================
# webserver to catch code
# ====================================================================================
"""
if settings.USER_IMPLICIT_GRANT_FLOW_CODE == '':

    def setup_simple_tcp_server_task():

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
                    super().do_GET()

            def log_request(self, code='-', size='-'):
                self.log_message('"%s" %s %s', self.requestline, str(code), str(size))
                if isinstance(code, HTTPStatus):
                    code = code.value
                # Stop the server if we get USER_IMPLICIT_GRANT_FLOW code back
                if "code" in self.path:
                    code = str(self.path.split("=")[1]).replace('&scope', '')
                    settings.USER_IMPLICIT_GRANT_FLOW_CODE = code
                    print("USER_IMPLICIT_GRANT_FLOW_CODE: done")  # ", settings.USER_IMPLICIT_GRANT_FLOW_CODE)
                    self.server.stop = True

        class ThreadingTCPServerWithStop(socketserver.ThreadingTCPServer):
            def server_bind(self):
                self.stop = False
                super().server_bind()

            def serve_forever(self, poll_interval=0.1):
                while not self.stop:
                    self.handle_request()

        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        with ThreadingTCPServerWithStop(("0.0.0.0", 3000), CodeHandler) as tcpserver:
            logger.info(f"Serving on {tcpserver.server_address}...")
            tcpserver.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if tcpserver.stop is not True:
                tcpserver.stop = False
                tcpserver.serve_forever(poll_interval=0.01)
            logger.info('Server stopped')

    setup_simple_tcp_server_task()

"""
# ====================================================================================
# OAUTH Step 2 use code to get token
# ====================================================================================
"""

if settings.USER_IMPLICIT_GRANT_FLOW_ACCESS_TOKEN == '':
    # Use code to get access_token and refresh_token from https://id.twitch.tv/oauth2/token
    async def get_access_token():
        igf = TwitchImplicitGrantFlow()
        token = await igf.obtain_access_token(code=settings.USER_IMPLICIT_GRANT_FLOW_CODE,
                                              redirect_uri='http://localhost:3000/auth')
        settings.USER_IMPLICIT_GRANT_FLOW_ACCESS_TOKEN = token['access_token']
        settings.USER_IMPLICIT_GRANT_FLOW_REFRESH_TOKEN = token['refresh_token']
    loop.run_until_complete(get_access_token())

# Wait until settings.USER_IMPLICIT_GRANT_FLOW_CODE is set
while settings.USER_IMPLICIT_GRANT_FLOW_ACCESS_TOKEN == '' \
  and settings.USER_IMPLICIT_GRANT_FLOW_REFRESH_TOKEN == '':
    pass
