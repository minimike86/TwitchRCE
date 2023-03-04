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
