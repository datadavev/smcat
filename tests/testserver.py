"""
Runs a simple web server for testing.

Serves content in the data folder relative to the location of this file.
"""
import time
import pathlib
import threading
import socketserver
import http.server
import urllib.parse

TEST_PORT = 8001
TEST_HOME = pathlib.Path(globals().get("__file__", "./_")).absolute().parent / "data"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=TEST_HOME, **kwargs)
        self.extensions_map[".jsonld"] = "application/ld+json"

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query_string = parsed.query
        path = parsed.path
        super().do_GET()


class TestServer(threading.Thread):

    def __init__(self, *args, **kwargs):
        self._port = kwargs.pop("port", TEST_PORT)
        super().__init__(*args, **kwargs)

    def run(self):
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", self._port), Handler)
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()

    def getAddress(self):
        return f"http://127.0.0.1:{self._port}/"


def runTestServer():
    with socketserver.TCPServer(("", TEST_PORT), Handler) as httpd:
        print(f"Test server at http://127.0.0.1:{TEST_PORT}/")
        httpd.serve_forever()


if __name__ == "__main__":
    runTestServer()
