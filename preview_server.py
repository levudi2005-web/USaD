"""Serve the static UI and proxy its API requests to the verified host backend."""

import http.client
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


WORKSPACE = Path(__file__).resolve().parent
BACKEND_HOST = "host.docker.internal"
BACKEND_PORT = 8000
MAX_REQUEST_BYTES = 1_048_576


class PreviewHandler(SimpleHTTPRequestHandler):
    PUBLIC_FILES = {"/index.html", "/styles.css", "/app.js"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WORKSPACE), **kwargs)

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def do_PATCH(self):
        self._dispatch("PATCH")

    def do_HEAD(self):
        self._dispatch("HEAD")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Allow", "GET, POST, PATCH, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _dispatch(self, method):
        request_path = urlsplit(self.path).path
        if request_path.startswith("/api/v1/"):
            self._proxy_api(method)
            return
        if request_path == "/":
            self.path = "/index.html"
            request_path = "/index.html"
        if request_path in self.PUBLIC_FILES and method in {"GET", "HEAD"}:
            if method == "HEAD":
                super().do_HEAD()
            else:
                super().do_GET()
            return
        self.send_error(404 if method in {"GET", "HEAD"} else 405)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_head(self):
        if self.headers.get("If-Modified-Since"):
            del self.headers["If-Modified-Since"]
        return super().send_head()

    def _proxy_api(self, method):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400, "Invalid Content-Length")
            return

        if length < 0 or length > MAX_REQUEST_BYTES:
            self.send_error(413, "Request body is too large")
            return

        body = self.rfile.read(length) if length else None
        headers = {
            key: self.headers[key]
            for key in ("Accept", "Authorization", "Content-Type")
            if self.headers.get(key) is not None
        }
        connection = http.client.HTTPConnection(
            BACKEND_HOST,
            BACKEND_PORT,
            timeout=8,
        )
        try:
            connection.request(method, self.path, body=body, headers=headers)
            response = connection.getresponse()
            response_body = response.read()
            self.send_response(response.status, response.reason)
            content_type = response.getheader("Content-Type")
            if content_type:
                self.send_header("Content-Type", content_type)
            cache_control = response.getheader("Cache-Control")
            if cache_control:
                self.send_header("Cache-Control", cache_control)
            self.send_header("Content-Length", str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)
        except OSError:
            self.log_error("Backend proxy request failed for %s", urlsplit(self.path).path)
            self.send_error(502, "Backend API is unreachable from the preview server")
        finally:
            connection.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=4173)
    arguments = parser.parse_args()
    server = ThreadingHTTPServer((arguments.host, arguments.port), PreviewHandler)
    print(
        f"USaD preview serving {WORKSPACE} on {arguments.host}:{arguments.port}; "
        f"API proxy -> {BACKEND_HOST}:{BACKEND_PORT}",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Preview server stopped.", flush=True)
    finally:
        server.server_close()
