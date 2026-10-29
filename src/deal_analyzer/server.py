"""Local web app: `deal-analyzer serve`.

Stdlib only. Serves a single page and a small JSON API backed by the same
engine as the CLI, so the numbers in the browser always match the terminal.

    GET  /                    the app
    GET  /api/schema          input fields + defaults for every kind
    GET  /api/samples         sample inputs for every kind
    POST /api/run/<kind>      body: inputs JSON -> result JSON
    POST /api/sensitivity     body: {kind, inputs, metric, x_field, x_values, y_field, y_values}
"""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources

from .finance import clean
from .kinds import KINDS, run, schema
from .samples import SAMPLES
from .sensitivity import sensitivity

MAX_BODY = 1_000_000
MAX_GRID_CELLS = 400


def _page() -> bytes:
    return resources.files("deal_analyzer").joinpath("web/index.html").read_bytes()


class Handler(BaseHTTPRequestHandler):
    server_version = "deal-analyzer"

    def log_message(self, fmt, *args):  # quieter default logging
        pass

    def _send(self, status: int, body: bytes, ctype: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, obj) -> None:
        self._send(status, json.dumps(clean(obj)).encode(), "application/json")

    def _error(self, status: int, message: str) -> None:
        self._json(status, {"error": message})

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            return self._send(HTTPStatus.OK, _page(), "text/html; charset=utf-8")
        if self.path == "/api/schema":
            return self._json(HTTPStatus.OK, schema())
        if self.path == "/api/samples":
            return self._json(HTTPStatus.OK, SAMPLES)
        return self._error(HTTPStatus.NOT_FOUND, f"No page at {self.path}")

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise ValueError("Request is too large")
        data = json.loads(self.rfile.read(length) or b"{}")
        if not isinstance(data, dict):
            raise ValueError("Send a JSON object")
        return data

    def do_POST(self):
        try:
            body = self._body()
        except (ValueError, json.JSONDecodeError) as e:
            return self._error(HTTPStatus.BAD_REQUEST, f"Couldn't read the request: {e}")

        try:
            if self.path.startswith("/api/run/"):
                kind = self.path.rsplit("/", 1)[-1]
                if kind not in KINDS:
                    return self._error(HTTPStatus.NOT_FOUND, f"Unknown analysis {kind!r}")
                return self._json(HTTPStatus.OK, run(kind, body))

            if self.path == "/api/sensitivity":
                xs, ys = body.get("x_values") or [], body.get("y_values") or []
                if len(xs) * len(ys) > MAX_GRID_CELLS:
                    return self._error(HTTPStatus.BAD_REQUEST, f"Keep the grid under {MAX_GRID_CELLS} cells")
                grid = sensitivity(body["kind"], body.get("inputs", {}), body["metric"],
                                   body["x_field"], [float(v) for v in xs],
                                   body["y_field"], [float(v) for v in ys])
                return self._json(HTTPStatus.OK, grid.to_dict())
        except KeyError as e:
            return self._error(HTTPStatus.BAD_REQUEST, str(e.args[0]) if e.args else "Missing field")
        except (TypeError, ValueError, ZeroDivisionError) as e:
            return self._error(HTTPStatus.BAD_REQUEST, f"Check the inputs: {e}")

        return self._error(HTTPStatus.NOT_FOUND, f"No endpoint at {self.path}")


def make_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), Handler)


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    httpd = make_server(host, port)
    print(f"deal-analyzer running at http://{host}:{httpd.server_address[1]}  (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
