"""HTTP front of camgate: still, live MJPEG and status on loopback. Fails closed."""
import http.server
import json
import logging
from typing import Callable

from .camera import CameraError
from .config import PORT
from .live import Busy, Cooldown, Private

log = logging.getLogger("camgate.server")

BOUNDARY = "frame"


def _visitor(headers) -> str:
    first = (headers.get("X-Forwarded-For") or "").split(",")[0].strip()
    return first or "anon"


class _Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "camgate"

    # -- plumbing ------------------------------------------------------------
    def log_message(self, fmt, *args):
        log.debug("%s %s", self.address_string(), fmt % args)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        if self.path.startswith("/cam/"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _json(self, code, obj, headers=(), body=True):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        for k, v in headers:
            self.send_header(k, v)
        self.end_headers()
        if body:
            self.wfile.write(data)

    def _route(self):
        return self.path.split("?", 1)[0]

    def do_GET(self):
        self._dispatch(head=False)

    def do_HEAD(self):
        self._dispatch(head=True)

    def _dispatch(self, head):
        route = self._route()
        try:
            if route == "/cam/status.json":
                self._json(200, self.server.status_fn(), body=not head)
            elif route == "/cam/still.jpg":
                self._still(head)
            elif route == "/cam/live.mjpg":
                self._live_head() if head else self._live()
            else:
                self._json(404, {"error": "not_found"}, body=not head)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True
        except Exception:
            log.exception("request failed: %s", self.path)
            self.close_connection = True
            try:
                self._json(500, {"error": "internal"}, headers=[("Connection", "close")], body=not head)
            except Exception:
                pass

    # -- routes --------------------------------------------------------------
    def _still(self, head):
        data, _ = self.server.keeper.current()
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if not head:
            self.wfile.write(data)

    def _live_headers(self):
        return [("X-Accel-Buffering", "no"), ("Connection", "close")]

    def _live_head(self):
        # Judged from the current decision and free slots; never opens a session.
        st = self.server.status_fn()
        self.close_connection = True
        if not st.get("public"):
            self._json(403, {"error": "private"}, self._live_headers(), body=False)
        elif st.get("live_slots_free", 0) <= 0:
            self._json(429, {"error": "busy"}, self._live_headers(), body=False)
        else:
            self._live_ok_headers()

    def _live_ok_headers(self):
        self.send_response(200)
        self.send_header("Content-Type", f"multipart/x-mixed-replace; boundary={BOUNDARY}")
        for k, v in self._live_headers():
            self.send_header(k, v)
        self.end_headers()

    def _live(self):
        self.close_connection = True
        hub = self.server.hub
        hdrs = self._live_headers()
        try:
            session = hub.open_session(_visitor(self.headers))
        except Private:
            return self._json(403, {"error": "private"}, hdrs)
        except (Busy, Cooldown) as e:
            kind = "busy" if isinstance(e, Busy) else "cooldown"
            return self._json(
                429,
                {"error": kind, "retry_after_s": int(e.retry_after_s)},
                hdrs + [("Retry-After", str(int(e.retry_after_s)))],
            )
        try:
            frames = session.frames()
            try:
                first = next(frames)
            except StopIteration:
                return self._json(403, {"error": "private"}, hdrs)  # ended before any frame
            except CameraError:
                return self._json(503, {"error": "camera_unavailable"}, hdrs)
            self._live_ok_headers()
            self._send_part(first)
            for jpeg in frames:
                self._send_part(jpeg)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            session.close()

    def _send_part(self, jpeg: bytes):
        self.wfile.write(
            b"--%s\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n" % (BOUNDARY.encode(), len(jpeg))
            + jpeg
            + b"\r\n"
        )
        self.wfile.flush()


class _Server(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def make_server(keeper, hub, status_fn: Callable[[], dict], host="127.0.0.1", port=PORT):
    srv = _Server((host, port), _Handler)
    srv.keeper, srv.hub, srv.status_fn = keeper, hub, status_fn
    return srv
