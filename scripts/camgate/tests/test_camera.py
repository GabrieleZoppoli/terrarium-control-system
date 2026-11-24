import io
import unittest

from PIL import Image

from camgate.camera import CameraError, StillKeeper
from camgate.config import Crop
from camgate.frames import placeholder_jpeg
from camgate.policy import Decision

PUBLIC = Decision(True, "ok")
PRIVATE = Decision(False, "doors_open")
CROP = Crop(1344, 1080, 0, 0)


def frame(w=1920, h=1080):
    img = Image.new("RGB", (w, h), (10, 120, 30))
    for x in range(0, w, 40):
        for y in range(0, h, 40):
            if (x // 40 + y // 40) % 2:
                img.paste((200, 30, 30), (x, y, x + 20, y + 20))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def size(jpeg):
    with Image.open(io.BytesIO(jpeg)) as im:
        return im.size


class FakeSource:
    def __init__(self, data=None):
        self.data = data if data is not None else frame()
        self.calls = 0
        self.error = None
        self.on_fetch = None

    def fetch(self):
        self.calls += 1
        if self.on_fetch:
            self.on_fetch()
        if self.error:
            raise self.error
        return self.data


class Harness:
    def __init__(self, source=None, crop=CROP):
        self.now = 0.0
        self.decision = PUBLIC
        self.crop = crop
        self.source = source or FakeSource()
        self.keeper = StillKeeper(
            self.source, lambda t: self.decision, lambda: self.crop, clock=lambda: self.now
        )


class StillKeeperTest(unittest.TestCase):
    def test_captures_when_public_and_due(self):
        h = Harness()
        h.keeper.tick()
        data, taken = h.keeper.current()
        self.assertEqual(size(data), (1344, 1080))
        self.assertEqual(taken, 0)

    def test_no_capture_when_private(self):
        h = Harness()
        h.decision = PRIVATE
        h.keeper.tick()
        data, taken = h.keeper.current()
        self.assertEqual(h.source.calls, 0)
        self.assertIsNone(taken)
        self.assertEqual(data, placeholder_jpeg())

    def test_refresh_interval(self):
        h = Harness()
        h.keeper.tick()
        h.now = 100
        h.keeper.tick()
        self.assertEqual(h.source.calls, 1)
        h.now = 181
        h.keeper.tick()
        self.assertEqual(h.source.calls, 2)

    def test_private_serves_blurred_last_still(self):
        h = Harness()
        h.keeper.tick()
        stored, _ = h.keeper.current()
        h.decision = PRIVATE
        h.now = 5
        data, taken = h.keeper.current()
        self.assertNotEqual(data, stored)
        self.assertEqual(size(data), (1344, 1080))
        self.assertEqual(taken, 0)

    def test_blurred_still_is_crop_size_not_full_frame(self):
        h = Harness()
        h.keeper.tick()
        h.decision = PRIVATE
        data, _ = h.keeper.current()
        self.assertEqual(size(data), (1344, 1080))
        self.assertNotEqual(size(data), (1920, 1080))

    def test_blur_is_cached(self):
        h = Harness()
        h.keeper.tick()
        h.decision = PRIVATE
        a, _ = h.keeper.current()
        b, _ = h.keeper.current()
        self.assertIs(a, b)

    def test_frame_discarded_if_door_opened_during_fetch(self):
        h = Harness()
        h.source.on_fetch = lambda: setattr(h, "decision", PRIVATE)
        h.keeper.tick()
        data, taken = h.keeper.current()
        self.assertIsNone(taken)
        self.assertEqual(data, placeholder_jpeg())

    def test_discarded_frame_keeps_previous_still(self):
        h = Harness()
        h.keeper.tick()
        h.now = 200
        h.source.on_fetch = lambda: setattr(h, "decision", PRIVATE)
        h.keeper.tick()
        _, taken = h.keeper.current()
        self.assertEqual(taken, 0)

    def test_crop_invalid_after_fetch_discards(self):
        h = Harness()
        h.source.on_fetch = lambda: setattr(h, "crop", None)
        h.keeper.tick()
        self.assertIsNone(h.keeper.current()[1])

    def test_source_failure_keeps_last_still(self):
        h = Harness()
        h.keeper.tick()
        good, _ = h.keeper.current()
        h.source.error = CameraError("down")
        h.now = 200
        h.keeper.tick()
        data, taken = h.keeper.current()
        self.assertEqual(data, good)
        self.assertEqual(taken, 0)

    def test_failed_fetch_retries_next_tick(self):
        h = Harness()
        h.source.error = CameraError("down")
        h.keeper.tick()
        h.source.error = None
        h.now = 1
        h.keeper.tick()
        self.assertEqual(h.source.calls, 2)
        self.assertEqual(h.keeper.current()[1], 1)

    def test_frame_smaller_than_crop_does_not_raise(self):
        h = Harness(FakeSource(frame(640, 480)))
        h.keeper.tick()
        data, taken = h.keeper.current()
        self.assertIsNone(taken)
        self.assertEqual(data, placeholder_jpeg())

    def test_taken_at_is_fetch_start(self):
        h = Harness()
        h.source.on_fetch = lambda: setattr(h, "now", 3.0)
        h.keeper.tick()
        self.assertEqual(h.keeper.current()[1], 0)

    def test_current_rechecks_policy(self):
        h = Harness()
        h.keeper.tick()
        public, _ = h.keeper.current()
        h.decision = PRIVATE
        self.assertNotEqual(h.keeper.current()[0], public)
        h.decision = PUBLIC
        self.assertEqual(h.keeper.current()[0], public)


if __name__ == "__main__":
    unittest.main()
