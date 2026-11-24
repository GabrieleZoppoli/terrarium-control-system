import io
import logging
import threading
import time
import unittest
from unittest import mock

from PIL import Image

from camgate.camera import CameraError
from camgate import live
from camgate.config import LIVE_COOLDOWN_S, LIVE_MAX_VIEWERS, LIVE_SESSION_S, Crop
from camgate.live import Busy, Cooldown, LiveHub, Private
from camgate.policy import Decision

logging.getLogger("camgate").addHandler(logging.NullHandler())

PUBLIC = Decision(True, "ok")
PRIVATE = Decision(False, "doors_open")
CROP = Crop(1344, 1080, 0, 0)


def frame(n, w=1920, h=1080):
    img = Image.new("RGB", (w, h), (10, 120, 30))
    for x in range(0, w, 80):
        img.paste(((n * 37) % 256, 30, 30), (x, 0, x + 40, h))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return buf.getvalue()


FRAMES = [frame(i) for i in range(4)]


def size(jpeg):
    with Image.open(io.BytesIO(jpeg)) as im:
        return im.size


class FakeSource:
    """Yields synthetic 1920x1080 JPEGs forever (or fails / stalls on request)."""

    def __init__(self, fail_after=None, stall_after=None, period=0.01):
        self.calls = 0
        self.yielded = 0
        self.fail_after = fail_after
        self.stall_after = stall_after
        self.period = period
        self.release = threading.Event()
        self.closed = threading.Event()

    def frames(self):
        self.calls += 1
        n = 0
        try:
            while True:
                if self.fail_after is not None and n >= self.fail_after:
                    raise CameraError("fake stream broke")
                if self.stall_after is not None and n >= self.stall_after:
                    self.release.wait()
                    return
                yield FRAMES[n % len(FRAMES)]
                self.yielded += 1
                n += 1
                time.sleep(self.period)
        finally:
            self.closed.set()


class Harness:
    def __init__(self, source=None, **kw):
        self.now = 0.0
        self.decision = PUBLIC
        self.crop = CROP
        self.source = source or FakeSource()
        self.hub = LiveHub(
            self.source,
            lambda t: self.decision,
            lambda: self.crop,
            clock=lambda: self.now,
            **kw,
        )


class LiveHubTest(unittest.TestCase):
    def setUp(self):
        self.harnesses = []

    def tearDown(self):
        for h in self.harnesses:
            h.source.release.set()
            for s in list(h.hub._sessions):
                s.close()

    def make(self, **kw):
        h = Harness(**kw)
        self.harnesses.append(h)
        return h

    def test_session_ends_at_backstop(self):
        h = self.make()
        s = h.hub.open_session("a")
        it = s.frames()
        next(it)
        h.now = LIVE_SESSION_S - 1.0
        next(it)
        h.now = LIVE_SESSION_S + 0.5
        with self.assertRaises(StopIteration):
            next(it)
        self.assertEqual(h.hub.slots_free(), LIVE_MAX_VIEWERS)

    def test_stream_stops_when_private(self):
        h = self.make()
        s = h.hub.open_session("a")
        it = s.frames()
        next(it)
        h.decision = PRIVATE
        with self.assertRaises(StopIteration):
            next(it)
        with self.assertRaises(StopIteration):
            next(it)
        self.assertEqual(h.hub.slots_free(), LIVE_MAX_VIEWERS)

    def test_stream_stops_when_crop_becomes_invalid(self):
        h = self.make()
        it = h.hub.open_session("a").frames()
        next(it)
        h.crop = None
        with self.assertRaises(StopIteration):
            next(it)

    def test_stream_stops_when_crop_exceeds_frame(self):
        h = self.make()
        h.crop = Crop(2000, 1080, 0, 0)
        it = h.hub.open_session("a").frames()
        with self.assertRaises(StopIteration):
            next(it)

    def test_private_detected_while_camera_stalled(self):
        h = self.make(source=FakeSource(stall_after=1))
        it = h.hub.open_session("a").frames()
        next(it)
        h.decision = PRIVATE
        t0 = time.monotonic()
        with self.assertRaises(StopIteration):
            next(it)
        self.assertLess(time.monotonic() - t0, 1.0)

    def test_deadline_detected_while_camera_stalled(self):
        h = self.make(source=FakeSource(stall_after=1))
        it = h.hub.open_session("a").frames()
        next(it)
        h.now = LIVE_SESSION_S + 1.0
        t0 = time.monotonic()
        with self.assertRaises(StopIteration):
            next(it)
        self.assertLess(time.monotonic() - t0, 1.0)

    def test_frames_are_cropped(self):
        h = self.make()
        it = h.hub.open_session("a").frames()
        for _ in range(3):
            self.assertEqual(size(next(it)), (1344, 1080))

    def test_frame_rate_limited(self):
        h = self.make()
        it = h.hub.open_session("a").frames()
        next(it)
        t0 = time.monotonic()
        for _ in range(3):
            next(it)
        self.assertGreaterEqual(time.monotonic() - t0, 0.95)

    def test_cap_rejects_extra_viewer(self):
        h = self.make()
        for v in ("a", "b", "c"):
            h.hub.open_session(v)
        self.assertEqual(h.hub.slots_free(), 0)
        h.now = 10.0
        with self.assertRaises(Busy) as cm:
            h.hub.open_session("d")
        self.assertEqual(cm.exception.retry_after_s, LIVE_SESSION_S - 10)

    def test_max_viewers_override(self):
        h = self.make(max_viewers=1)
        h.hub.open_session("a")
        with self.assertRaises(Busy):
            h.hub.open_session("b")

    def test_busy_retry_after_floored_at_1(self):
        h = self.make(max_viewers=1)
        h.hub.open_session("a")
        h.now = LIVE_SESSION_S - 0.1
        with self.assertRaises(Busy) as cm:
            h.hub.open_session("b")
        self.assertEqual(cm.exception.retry_after_s, 1)
        self.assertIsInstance(cm.exception.retry_after_s, int)

    def test_cooldown_blocks_immediate_restart(self):
        h = self.make()
        s = h.hub.open_session("a")
        h.now = 5.0
        s.close()
        with self.assertRaises(Cooldown) as cm:
            h.hub.open_session("a")
        self.assertEqual(cm.exception.retry_after_s, LIVE_COOLDOWN_S)
        h.hub.open_session("b")  # other visitors unaffected
        h.now = 5.0 + LIVE_COOLDOWN_S
        h.hub.open_session("a")

    def test_cooldown_after_timeout(self):
        h = self.make()
        it = h.hub.open_session("a").frames()
        next(it)
        h.now = LIVE_SESSION_S + 1.0
        with self.assertRaises(StopIteration):
            next(it)
        with self.assertRaises(Cooldown):
            h.hub.open_session("a")

    def test_cooldown_retry_s_is_read_only(self):
        h = self.make()
        self.assertIsNone(h.hub.cooldown_retry_s("a"))
        s = h.hub.open_session("a")
        h.now = 5.0
        s.close()
        h.now = 6.5
        for _ in range(3):  # repeated reads neither consume nor extend it
            self.assertEqual(h.hub.cooldown_retry_s("a"), LIVE_COOLDOWN_S - 1)
        self.assertIsNone(h.hub.cooldown_retry_s("b"))
        with self.assertRaises(Cooldown) as cm:
            h.hub.open_session("a")
        self.assertEqual(cm.exception.retry_after_s, LIVE_COOLDOWN_S - 1)
        h.now = 5.0 + LIVE_COOLDOWN_S
        self.assertIsNone(h.hub.cooldown_retry_s("a"))
        h.hub.open_session("a")

    def test_busy_retry_s_is_soonest_session_end(self):
        h = self.make(max_viewers=2)
        h.hub.open_session("a")
        h.now = 10.0
        h.hub.open_session("b")
        h.now = 12.0
        self.assertEqual(h.hub.busy_retry_s(), LIVE_SESSION_S - 12)  # "a" ends first
        self.assertEqual(h.hub.slots_free(), 0)  # read-only: nothing opened or ended
        with self.assertRaises(Busy) as cm:
            h.hub.open_session("c")
        self.assertEqual(cm.exception.retry_after_s, LIVE_SESSION_S - 12)

    def test_busy_retry_s_floor_without_sessions(self):
        h = self.make()
        self.assertEqual(h.hub.busy_retry_s(), 1)

    def test_private_rejects_open(self):
        h = self.make()
        h.decision = PRIVATE
        with self.assertRaises(Private):
            h.hub.open_session("a")
        h.decision = PUBLIC
        h.crop = None
        with self.assertRaises(Private):
            h.hub.open_session("a")
        self.assertEqual(h.source.calls, 0)

    def test_private_checked_before_cooldown_and_cap(self):
        h = self.make(max_viewers=1)
        h.hub.open_session("a").close()
        h.hub.open_session("b")
        h.decision = PRIVATE
        with self.assertRaises(Private):
            h.hub.open_session("a")
        with self.assertRaises(Private):
            h.hub.open_session("c")

    def test_single_reader_for_many_viewers(self):
        h = self.make()
        its = [h.hub.open_session(v).frames() for v in ("a", "b", "c")]
        for _ in range(2):
            for it in its:
                self.assertEqual(size(next(it)), (1344, 1080))
        self.assertEqual(h.source.calls, 1)

    def test_reader_stops_when_idle(self):
        h = self.make()
        sessions = [h.hub.open_session(v) for v in ("a", "b")]
        next(sessions[0].frames())
        thread = h.hub._thread
        self.assertTrue(thread.is_alive())
        sessions[0].close()
        self.assertTrue(thread.is_alive())
        sessions[1].close()
        thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertTrue(h.source.closed.is_set())

    def test_source_failure_ends_sessions(self):
        h = self.make(source=FakeSource(fail_after=2))
        with self.assertLogs("camgate.live", "WARNING") as logs:
            sessions = [h.hub.open_session(v) for v in ("a", "b")]
            it = sessions[0].frames()
            next(it)
            with self.assertRaises(StopIteration):
                while True:
                    next(it)
        self.assertIn("fake stream broke", "\n".join(logs.output))
        self.assertEqual(h.hub.slots_free(), LIVE_MAX_VIEWERS)
        with self.assertRaises(CameraError):
            next(sessions[1].frames())
        # A later visitor gets a fresh reader.
        h.source.fail_after = None
        it2 = h.hub.open_session("c").frames()
        self.assertEqual(size(next(it2)), (1344, 1080))
        self.assertEqual(h.source.calls, 2)

    def test_startup_timeout_raises_camera_error(self):
        h = self.make(source=FakeSource(stall_after=0), startup_timeout_s=0.3)
        it = h.hub.open_session("a").frames()
        t0 = time.monotonic()
        with self.assertRaises(CameraError):
            next(it)
        self.assertLess(time.monotonic() - t0, 1.0)
        self.assertEqual(h.hub.slots_free(), LIVE_MAX_VIEWERS)

    def test_frame_cropped_with_stale_crop_is_not_sent(self):
        h = self.make()
        it = h.hub.open_session("a").frames()
        next(it)
        h.crop = Crop(1000, 800, 0, 0)
        self.assertEqual(size(next(it)), (1000, 800))

    def _counting_crop(self):
        calls = []
        real = live.crop_jpeg

        def counting(jpeg, crop):
            calls.append(crop)
            return real(jpeg, crop)

        return calls, mock.patch.object(live, "crop_jpeg", counting)

    def test_crop_work_bounded_by_frames_sent(self):
        calls, patch = self._counting_crop()
        with patch:
            h = self.make(source=FakeSource(period=0.002))
            its = [h.hub.open_session(v).frames() for v in ("a", "b", "c")]
            sent = 0
            for _ in range(3):
                for it in its:
                    next(it)
                    sent += 1
        self.assertGreater(h.source.yielded, 3 * len(calls))
        self.assertLessEqual(len(calls), sent)

    def test_no_crop_work_for_idle_session(self):
        calls, patch = self._counting_crop()
        with patch:
            h = self.make(source=FakeSource(period=0.002))
            h.hub.open_session("a")
            deadline = time.monotonic() + 2
            while h.source.yielded < 50 and time.monotonic() < deadline:
                time.sleep(0.01)
        self.assertGreaterEqual(h.source.yielded, 50)
        self.assertEqual(calls, [])

    def test_crop_changed_during_cropping_is_not_served(self):
        h = self.make()
        real = live.crop_jpeg
        new = Crop(1000, 800, 0, 0)
        crops = []

        def flipping(jpeg, crop):
            crops.append(crop)
            out = real(jpeg, crop)
            h.crop = new  # crop_fn changes while the old crop is being applied
            return out

        with mock.patch.object(live, "crop_jpeg", flipping):
            it = h.hub.open_session("a").frames()
            self.assertEqual(size(next(it)), (1000, 800))
        self.assertEqual(crops[0], CROP)

    def test_three_concurrent_viewers_each_stream(self):
        """Regression: with 3 viewers in their own threads each got 1 frame, then the stream ended."""
        h = self.make(source=FakeSource(period=0.125))  # ~8 fps like ustreamer
        sessions = [h.hub.open_session(v) for v in ("a", "b", "c")]
        counts = [0, 0, 0]
        stop = time.monotonic() + 2.5

        def consume(i):
            for jpeg in sessions[i].frames():
                self.assertEqual(size(jpeg), (1344, 1080))
                counts[i] += 1
                if time.monotonic() >= stop:
                    break

        threads = [threading.Thread(target=consume, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()
        time.sleep(1.5)
        self.assertEqual(h.hub.slots_free(), 0)  # all three still streaming
        with self.assertRaises(Busy):
            h.hub.open_session("d")
        for t in threads:
            t.join(5)
        for c in counts:
            self.assertGreaterEqual(c, 5, counts)


if __name__ == "__main__":
    unittest.main()
