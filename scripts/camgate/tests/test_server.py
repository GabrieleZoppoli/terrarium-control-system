import http.client
import io
import json
import logging
import os
import socket
import threading
import time
import unittest

from PIL import Image

import inspect

from camgate.__main__ import TICK_S, make_cached_crop_fn, make_status_fn, tick_loop
from camgate.camera import StillKeeper
from camgate.config import LIVE_COOLDOWN_S, LIVE_SESSION_S, Crop, NO_CROP
from camgate.frames import placeholder_jpeg
from camgate.live import LiveHub
from camgate.policy import Decision, DoorSignal, ShowMe
from camgate.server import _visitor, make_server
from camgate.signals import SignalStore

logging.getLogger("camgate").addHandler(logging.NullHandler())

PUBLIC = Decision(True, "ok")
PRIVATE = Decision(False, "doors_open")
CROP = Crop(1344, 1080, 0, 0)


def _frame(n):
    img = Image.new("RGB", (1920, 1080), (10, 120, 30))
    img.paste(((n * 37) % 256, 30, 30), (0, 0, 400, 1080))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return buf.getvalue()


FRAMES = [_frame(i) for i in range(3)]


def size(jpeg):
    with Image.open(io.BytesIO(jpeg)) as im:
        return im.size


class FakeSnap:
    def fetch(self):
        return FRAMES[0]


def _noisy_frame():
    img = Image.frombytes("RGB", (1920, 1080), os.urandom(1920 * 1080 * 3))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


class FakeStream:
    def __init__(self, fail=False, frames=None):
        self.fail = fail
        self._frames = frames or FRAMES

    def frames(self):
        if self.fail:
            from camgate.camera import CameraError

            raise CameraError("down")
        n = 0
        while True:
            yield self._frames[n % len(self._frames)]
            n += 1
            time.sleep(0.02)


class Env:
    def __init__(self, max_viewers=3, fail_stream=False, status_fn=None, timeout=10, stream_frames=None):
        self.decision = PUBLIC
        self.crop = CROP
        dec = lambda t: self.decision
        crop = lambda: self.crop
        self.keeper = StillKeeper(FakeSnap(), dec, crop)
        self.hub = LiveHub(FakeStream(fail_stream, stream_frames), dec, crop, max_viewers=max_viewers, startup_timeout_s=1.0)
        self.status = status_fn or (
            lambda: {
                "public": self.decision.public,
                "reason": self.decision.reason,
                "showme": False,
                "live_slots_free": self.hub.slots_free(),
                "still_taken_at": None,
            }
        )
        self.flowers = {"w": 1344, "h": 1080, "items": [{"num": 1, "state": "bud", "x": 5, "y": 6}]}
        self.gate_state = {"ok": True, "reason": "ok", "last_not_ok_at": 1.0, "now": 2.0}
        self.srv = make_server(
            self.keeper, self.hub, self.status, port=0, timeout=timeout, archive_gate_fn=lambda: self.gate_state,
            flowers_fn=lambda: self.flowers,
        )
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True).start()

    def close(self):
        self.srv.shutdown()
        self.srv.server_close()

    def conn(self):
        return http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)

    def get(self, path, method="GET", headers=None):
        c = self.conn()
        c.request(method, path, headers=headers or {})
        r = c.getresponse()
        body = r.read()
        c.close()
        return r, body


def read_part(resp):
    """Read one multipart part from an open live response; return jpeg bytes."""
    assert resp.fp.readline().strip() == b"--frame"
    assert resp.fp.readline().strip() == b"Content-Type: image/jpeg"
    n = int(resp.fp.readline().split(b":")[1])
    assert resp.fp.readline() == b"\r\n"
    data = resp.fp.read(n)
    assert resp.fp.readline() == b"\r\n"
    return data


class ServerTest(unittest.TestCase):
    def setUp(self):
        self.env = Env()
        self.addCleanup(self.env.close)

    def test_archive_gate_internal_route(self):
        r, body = self.env.get("/internal/archive-gate.json")
        self.assertEqual(r.status, 200)
        self.assertEqual(set(json.loads(body)), {"ok", "reason", "last_not_ok_at", "now"})

    def test_archive_gate_not_under_cam(self):
        r, _ = self.env.get("/cam/internal/archive-gate.json")
        self.assertEqual(r.status, 404)

    def test_flowers_route(self):
        r, body = self.env.get("/cam/flowers.json")
        self.assertEqual(r.status, 200)
        self.assertEqual(json.loads(body), self.env.flowers)
        self.assertEqual(r.getheader("Access-Control-Allow-Origin"), "*")

    def test_flowers_route_without_source_is_empty(self):
        srv = make_server(self.env.keeper, self.env.hub, self.env.status, port=0)
        self.addCleanup(srv.server_close)
        threading.Thread(target=srv.handle_request, daemon=True).start()
        c = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=5)
        c.request("GET", "/cam/flowers.json")
        self.assertEqual(json.loads(c.getresponse().read()), {"w": 0, "h": 0, "items": []})
        c.close()

    def test_status_json_shape(self):
        r, body = self.env.get("/cam/status.json")
        self.assertEqual(r.status, 200)
        self.assertEqual(set(json.loads(body)), {"public", "reason", "showme", "live_slots_free", "still_taken_at"})
        self.assertEqual(r.getheader("Access-Control-Allow-Origin"), "*")
        self.assertEqual(r.getheader("Cache-Control"), "no-store")

    def test_still_is_cropped(self):
        self.env.keeper.tick()
        r, body = self.env.get("/cam/still.jpg")
        self.assertEqual(r.status, 200)
        self.assertEqual(r.getheader("Content-Type"), "image/jpeg")
        self.assertEqual(r.getheader("Cache-Control"), "no-store")
        self.assertEqual(size(body), (1344, 1080))

    def test_still_head_has_no_body(self):
        r, body = self.env.get("/cam/still.jpg", method="HEAD")
        self.assertEqual((r.status, body), (200, b""))

    def test_live_private_is_403(self):
        self.env.decision = PRIVATE
        r, body = self.env.get("/cam/live.mjpg")
        self.assertEqual(r.status, 403)
        self.assertEqual(json.loads(body), {"error": "private"})
        self.assertEqual(r.getheader("Access-Control-Allow-Origin"), "*")
        self.assertEqual(r.getheader("Cache-Control"), "no-store")

    def test_live_busy_is_429_with_retry(self):
        env = Env(max_viewers=1)
        self.addCleanup(env.close)
        c = env.conn()
        c.request("GET", "/cam/live.mjpg", headers={"X-Forwarded-For": "1.1.1.1"})
        first = c.getresponse()
        self.assertEqual(first.status, 200)
        self.addCleanup(c.close)
        self.addCleanup(first.close)
        r, body = env.get("/cam/live.mjpg", headers={"X-Forwarded-For": "2.2.2.2"})
        self.assertEqual(r.status, 429)
        obj = json.loads(body)
        self.assertEqual(obj["error"], "busy")
        self.assertIsInstance(obj["retry_after_s"], int)
        self.assertEqual(r.getheader("Retry-After"), str(obj["retry_after_s"]))

    def test_live_cooldown_is_429(self):
        c = self.env.conn()
        c.request("GET", "/cam/live.mjpg", headers={"X-Forwarded-For": "6.6.6.6, 9.9.9.9"})
        resp = c.getresponse()
        read_part(resp)
        resp.close()
        c.close()
        for _ in range(50):  # wait until the server has noticed the close
            if self.env.hub.slots_free() == 3:
                break
            time.sleep(0.1)
        r, body = self.env.get("/cam/live.mjpg", headers={"X-Forwarded-For": "9.9.9.9"})
        self.assertEqual(r.status, 429)
        self.assertEqual(json.loads(body)["error"], "cooldown")

    def _watch_once(self, env, xff):
        c = env.conn()
        c.request("GET", "/cam/live.mjpg", headers={"X-Forwarded-For": xff})
        resp = c.getresponse()
        read_part(resp)
        resp.close()
        c.close()
        for _ in range(50):
            if env.hub.slots_free() == env.hub._max_viewers:
                break
            time.sleep(0.1)

    def test_live_head_cooldown_is_429_with_retry_after_and_not_consumed(self):
        self._watch_once(self.env, "9.9.9.9")
        for _ in range(2):
            r, body = self.env.get("/cam/live.mjpg", method="HEAD", headers={"X-Forwarded-For": "9.9.9.9"})
            self.assertEqual((r.status, body), (429, b""))
            self.assertEqual(r.getheader("X-Live-Refusal"), "cooldown")
            ra = int(r.getheader("Retry-After"))
            self.assertTrue(LIVE_COOLDOWN_S - 5 <= ra <= LIVE_COOLDOWN_S, ra)
        r, _ = self.env.get("/cam/live.mjpg", method="HEAD", headers={"X-Forwarded-For": "8.8.8.8"})
        self.assertEqual(r.status, 200)  # other visitors unaffected
        before = dict(self.env.hub._cooldowns)
        self.env.get("/cam/live.mjpg", method="HEAD", headers={"X-Forwarded-For": "9.9.9.9"})
        self.assertEqual(self.env.hub._cooldowns, before)  # HEAD never alters the cooldown
        r, body = self.env.get("/cam/live.mjpg", headers={"X-Forwarded-For": "9.9.9.9"})
        self.assertEqual(r.status, 429)
        self.assertEqual(json.loads(body)["error"], "cooldown")

    def test_live_head_busy_has_retry_after_soonest_end(self):
        env = Env(max_viewers=1)
        self.addCleanup(env.close)
        c = env.conn()
        c.request("GET", "/cam/live.mjpg", headers={"X-Forwarded-For": "1.1.1.1"})
        first = c.getresponse()
        self.assertEqual(first.status, 200)
        self.addCleanup(c.close)
        self.addCleanup(first.close)
        r, body = env.get("/cam/live.mjpg", method="HEAD", headers={"X-Forwarded-For": "2.2.2.2"})
        self.assertEqual((r.status, body), (429, b""))
        self.assertEqual(r.getheader("X-Live-Refusal"), "busy")
        ra = int(r.getheader("Retry-After"))
        self.assertTrue(LIVE_SESSION_S - 5 <= ra <= LIVE_SESSION_S, ra)
        self.assertEqual(env.hub.slots_free(), 0)

    def test_retry_after_exposed_to_cors_on_every_response(self):
        self.env.keeper.tick()
        for method, path in [("GET", "/cam/status.json"), ("GET", "/cam/still.jpg"),
                             ("HEAD", "/cam/live.mjpg"), ("GET", "/nope")]:
            r, _ = self.env.get(path, method=method)
            exposed = [h.strip() for h in (r.getheader("Access-Control-Expose-Headers") or "").split(",")]
            self.assertIn("Retry-After", exposed, path)
            self.assertIn("X-Live-Refusal", exposed, path)

    def test_visitor_is_rightmost_forwarded_for(self):
        self.assertEqual(_visitor({"X-Forwarded-For": "6.6.6.6, 9.9.9.9"}), "9.9.9.9")
        self.assertEqual(_visitor({"X-Forwarded-For": " 9.9.9.9 "}), "9.9.9.9")
        self.assertEqual(_visitor({"X-Forwarded-For": "1.1.1.1, 2.2.2.2 , , "}), "2.2.2.2")
        self.assertEqual(_visitor({"X-Forwarded-For": " , "}), "anon")
        self.assertEqual(_visitor({}), "anon")

    def test_spoofed_leftmost_forwarded_for_does_not_dodge_cooldown(self):
        self._watch_once(self.env, "9.9.9.9")
        r, body = self.env.get("/cam/live.mjpg", headers={"X-Forwarded-For": "1.2.3.4, 9.9.9.9"})
        self.assertEqual(r.status, 429)
        self.assertEqual(json.loads(body)["error"], "cooldown")

    def test_three_concurrent_live_clients_stream_and_fourth_is_busy(self):
        """Regression for the deploy test: 3 viewers each got 1 part and then the stream ended."""
        env = Env(stream_frames=FRAMES)
        self.addCleanup(env.close)
        counts = [0, 0, 0]
        stop = time.monotonic() + 2.5

        def viewer(i):
            c = env.conn()
            c.request("GET", "/cam/live.mjpg", headers={"X-Forwarded-For": f"10.9.7.{i}"})
            r = c.getresponse()
            if r.status != 200:
                return
            try:
                while time.monotonic() < stop:
                    self.assertEqual(size(read_part(r)), (1344, 1080))
                    counts[i] += 1
            finally:
                r.close()
                c.close()

        threads = [threading.Thread(target=viewer, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        time.sleep(1.5)
        r, body = env.get("/cam/live.mjpg", headers={"X-Forwarded-For": "10.9.7.99"})
        self.assertEqual(r.status, 429)
        self.assertEqual(json.loads(body)["error"], "busy")
        for t in threads:
            t.join(5)
        for n in counts:
            self.assertGreaterEqual(n, 5, counts)

    def test_live_camera_unavailable_is_503(self):
        env = Env(fail_stream=True)
        self.addCleanup(env.close)
        r, body = env.get("/cam/live.mjpg")
        self.assertEqual(r.status, 503)
        self.assertEqual(json.loads(body), {"error": "camera_unavailable"})
        self.assertEqual(env.hub.slots_free(), 3)

    def test_live_headers_and_close_frees_slot(self):
        c = self.env.conn()
        c.request("GET", "/cam/live.mjpg")
        r = c.getresponse()
        self.assertEqual(r.status, 200)
        self.assertEqual(r.getheader("Content-Type"), "multipart/x-mixed-replace; boundary=frame")
        self.assertEqual(r.getheader("X-Accel-Buffering"), "no")
        self.assertEqual(r.getheader("Cache-Control"), "no-store")
        self.assertEqual(r.getheader("Access-Control-Allow-Origin"), "*")
        read_part(r)
        self.assertEqual(self.env.hub.slots_free(), 2)
        r.close()
        c.close()
        for _ in range(50):
            if self.env.hub.slots_free() == 3:
                break
            time.sleep(0.1)
        self.assertEqual(self.env.hub.slots_free(), 3)

    def test_stalled_live_client_is_dropped_and_slot_freed(self):
        env = Env(timeout=1, stream_frames=[_noisy_frame()])
        self.addCleanup(env.close)
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
        sock.connect(("127.0.0.1", env.port))
        self.addCleanup(sock.close)
        sock.sendall(b"GET /cam/live.mjpg HTTP/1.1\r\nHost: x\r\n\r\n")  # then never read
        for _ in range(30):
            if env.hub.slots_free() < 3:
                break
            time.sleep(0.05)
        self.assertEqual(env.hub.slots_free(), 2)
        t0 = time.monotonic()
        while env.hub.slots_free() < 3 and time.monotonic() - t0 < 6:
            time.sleep(0.05)
        self.assertEqual(env.hub.slots_free(), 3)

    def test_idle_keepalive_connection_is_dropped(self):
        env = Env(timeout=0.5)
        self.addCleanup(env.close)
        sock = socket.create_connection(("127.0.0.1", env.port))
        self.addCleanup(sock.close)
        sock.settimeout(4)
        self.assertEqual(sock.recv(10), b"")  # server closed the idle connection

    def test_live_head_does_not_open_session(self):
        r, body = self.env.get("/cam/live.mjpg", method="HEAD")
        self.assertEqual((r.status, body), (200, b""))
        self.assertEqual(r.getheader("Content-Type"), "multipart/x-mixed-replace; boundary=frame")
        self.assertEqual(self.env.hub.slots_free(), 3)
        r2, _ = self.env.get("/cam/live.mjpg", method="HEAD")
        self.assertEqual(r2.status, 200)  # no cooldown consumed
        self.env.decision = PRIVATE
        r3, _ = self.env.get("/cam/live.mjpg", method="HEAD")
        self.assertEqual(r3.status, 403)

    def test_live_stream_ends_on_door_open(self):
        c = self.env.conn()
        c.request("GET", "/cam/live.mjpg")
        r = c.getresponse()
        read_part(r)
        self.env.decision = PRIVATE
        t0 = time.monotonic()
        try:
            while r.fp.read(65536):
                pass
        except Exception:
            pass
        self.assertLess(time.monotonic() - t0, 1.5)
        r.close()
        c.close()

    def test_every_route_is_cropped(self):
        self.env.keeper.tick()
        _, still = self.env.get("/cam/still.jpg")
        self.assertEqual(size(still), (1344, 1080))
        c = self.env.conn()
        c.request("GET", "/cam/live.mjpg")
        r = c.getresponse()
        for _ in range(3):
            self.assertEqual(size(read_part(r)), (1344, 1080))
        r.close()
        c.close()

    def test_startup_without_signals_serves_placeholder(self):
        store = SignalStore()
        crop = lambda: CROP
        dec = lambda now: __import__("camgate.policy", fromlist=["decide"]).decide(now, *store.snapshot(), crop())
        keeper = StillKeeper(FakeSnap(), dec, crop)
        hub = LiveHub(FakeStream(), dec, crop)
        env_srv = make_server(keeper, hub, make_status_fn(store, keeper, hub, crop), port=0)
        threading.Thread(target=env_srv.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True).start()
        self.addCleanup(env_srv.server_close)
        self.addCleanup(env_srv.shutdown)
        port = env_srv.server_address[1]

        def get(path):
            c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            c.request("GET", path)
            r = c.getresponse()
            body = r.read()
            c.close()
            return r, body

        keeper.tick()
        r, body = get("/cam/still.jpg")
        self.assertEqual(body, placeholder_jpeg())
        st = json.loads(get("/cam/status.json")[1])
        self.assertFalse(st["public"])
        self.assertEqual(st["reason"], "door_state_unknown")
        self.assertIsNone(st["still_taken_at"])
        self.assertEqual(get("/cam/live.mjpg")[0].status, 403)

    def test_unknown_path_404(self):
        r, _ = self.env.get("/nope")
        self.assertEqual(r.status, 404)
        self.assertEqual(r.getheader("Access-Control-Allow-Origin"), "*")
        r, _ = self.env.get("/cam/other")
        self.assertEqual(r.status, 404)
        self.assertEqual(r.getheader("Cache-Control"), "no-store")

    def test_status_error_is_500_not_leak(self):
        def boom():
            raise RuntimeError("x")

        env = Env(status_fn=boom)
        self.addCleanup(env.close)
        with self.assertLogs("camgate.server", level="ERROR"):
            r, body = env.get("/cam/status.json")
        self.assertEqual(r.status, 500)
        self.assertEqual(r.getheader("Access-Control-Allow-Origin"), "*")


class MainHelpersTest(unittest.TestCase):
    def test_status_fn_composition(self):
        store = SignalStore()
        store.set_connected(True)
        now = 1_000_000.0
        store.set_doors(DoorSignal(False, 1.0, now))
        store.set_showme(ShowMe(True, now + 100))
        crop = lambda: CROP
        keeper = StillKeeper(FakeSnap(), lambda t: Decision(True, "ok"), crop, clock=lambda: 1763979300.0)
        keeper.tick()
        hub = LiveHub(FakeStream(), lambda t: Decision(True, "ok"), crop, max_viewers=2)
        st = make_status_fn(store, keeper, hub, crop, clock=lambda: now)()
        self.assertEqual(st["public"], True)
        self.assertEqual(st["reason"], "showme")
        self.assertTrue(st["showme"])
        self.assertEqual(st["live_slots_free"], 2)
        self.assertEqual(st["still_taken_at"], "2025-11-24T10:15:00Z")
        # showme "on" but expired is not active
        store.set_showme(ShowMe(True, now - 1))
        st = make_status_fn(store, keeper, hub, crop, clock=lambda: now)()
        self.assertFalse(st["showme"])
        self.assertEqual(st["reason"], "ok")

    def test_crop_cache_rereads_after_ttl_and_catches_errors(self):
        t = [0.0]
        calls = []

        def loader(path):
            calls.append(path)
            if len(calls) == 3:
                raise OSError("boom")
            return CROP if len(calls) == 1 else NO_CROP

        fn = make_cached_crop_fn("/x", ttl=10, clock=lambda: t[0], loader=loader)
        self.assertEqual(fn(), CROP)
        t[0] = 9.9
        self.assertEqual(fn(), CROP)
        self.assertEqual(len(calls), 1)
        t[0] = 10.0
        self.assertIs(fn(), NO_CROP)
        t[0] = 20.0
        with self.assertLogs("camgate", level="ERROR"):
            self.assertIsNone(fn())

    def test_tick_interval_is_1s(self):
        # Ruling R16: a 1 s tick sees any private period of 1 s or longer, so the
        # held still is marked suspect; captures stay at STILL_REFRESH_S.
        self.assertEqual(TICK_S, 1.0)
        self.assertEqual(inspect.signature(tick_loop).parameters["interval"].default, TICK_S)

    def test_tick_loop_survives_exceptions(self):
        stop = threading.Event()
        n = []

        class K:
            def tick(self):
                n.append(1)
                if len(n) >= 3:
                    stop.set()
                raise RuntimeError("x")

        with self.assertLogs("camgate", level="ERROR"):
            tick_loop(K(), interval=0.01, stop=stop)
        self.assertEqual(len(n), 3)


if __name__ == "__main__":
    unittest.main()
