"""
Runs a simple web server for testing.

Serves content in the data folder relative to the location of this file.
"""
import os
import pathlib
import threading
import socketserver
import http.server
import urllib.parse
import datetime
import email
from http import HTTPStatus

TEST_PORT = 8001
TEST_HOME = pathlib.Path(globals().get("__file__", "./_")).absolute().parent / "data"


class Handler(http.server.SimpleHTTPRequestHandler):
    indexes = ["index.htm", ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=TEST_HOME, **kwargs)
        self.extensions_map[".jsonld"] = "application/ld+json"

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query_string = parsed.query
        path = parsed.path
        super().do_GET()

    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            parts = urllib.parse.urlsplit(self.path)
            if not parts.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(HTTPStatus.MOVED_PERMANENTLY)
                new_parts = (parts[0], parts[1], parts[2] + '/',
                             parts[3], parts[4])
                new_url = urllib.parse.urlunsplit(new_parts)
                self.send_header("Location", new_url)
                self.end_headers()
                return None
            for index in self.indexes:
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        # check for trailing "/" which should return 404. See Issue17324
        # The test for this was added in test_httpserver.py
        # However, some OS platforms accept a trailingSlash as a filename
        # See discussion on python-dev and Issue34711 regarding
        # parseing and rejection of filenames with a trailing slash
        if path.endswith("/"):
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None

        try:
            fs = os.fstat(f.fileno())
            # Use browser cache if possible
            if ("If-Modified-Since" in self.headers
                    and "If-None-Match" not in self.headers):
                # compare If-Modified-Since and time of last file modification
                try:
                    ims = email.utils.parsedate_to_datetime(
                        self.headers["If-Modified-Since"])
                except (TypeError, IndexError, OverflowError, ValueError):
                    # ignore ill-formed values
                    pass
                else:
                    if ims.tzinfo is None:
                        # obsolete format with no timezone, cf.
                        # https://tools.ietf.org/html/rfc7231#section-7.1.1.1
                        ims = ims.replace(tzinfo=datetime.timezone.utc)
                    if ims.tzinfo is datetime.timezone.utc:
                        # compare to UTC datetime of last modification
                        last_modif = datetime.datetime.fromtimestamp(
                            fs.st_mtime, datetime.timezone.utc)
                        # remove microseconds, like in If-Modified-Since
                        last_modif = last_modif.replace(microsecond=0)

                        if last_modif <= ims:
                            self.send_response(HTTPStatus.NOT_MODIFIED)
                            self.end_headers()
                            f.close()
                            return None

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", ctype)
            self.send_header("Content-Length", str(fs[6]))
            self.send_header("Last-Modified",
                self.date_time_string(fs.st_mtime))
            self.end_headers()
            return f
        except:
            f.close()
            raise


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
