import io
import unittest

import numpy as np
from PIL import Image

from camgate.config import Crop
from timelapse.lossless import (LosslessError, archive_geometry, crop_rotate,
                                mcu_size, snap_inward)

FRAME = (1920, 1080)


def make_jpeg():
    x = np.linspace(0, 255, 1920)[None, :, None]
    y = np.linspace(0, 255, 1080)[:, None, None]
    arr = np.concatenate([np.broadcast_to(x, (1080, 1920, 1)),
                          np.broadcast_to(y, (1080, 1920, 1)),
                          np.full((1080, 1920, 1), 90.0)], axis=2).astype("uint8")
    img = Image.fromarray(arr)
    img.paste((255, 0, 0), (100, 400, 150, 450))   # marker outside the crop
    img.paste((0, 255, 0), (700, 400, 750, 450))   # marker inside the crop
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80, subsampling=1)
    return buf.getvalue()


class LosslessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jpeg = make_jpeg()

    def test_mcu_422(self):
        self.assertEqual(mcu_size(self.jpeg), (16, 8))

    def test_snap_inward_current_crop(self):
        self.assertEqual(snap_inward(Crop(1180, 1080, 164, 0), (16, 8), FRAME),
                         Crop(1168, 1080, 176, 0))

    def test_snap_never_grows(self):
        for c in [Crop(1180, 1080, 164, 0), Crop(1344, 1080, 0, 0), Crop(1001, 999, 3, 5)]:
            s = snap_inward(c, (16, 8), FRAME)
            self.assertTrue(s.x >= c.x and s.y >= c.y and
                            s.x + s.w <= c.x + c.w and s.y + s.h <= c.y + c.h)
            self.assertEqual((s.x % 16, s.y % 8), (0, 0))

    def test_snap_none_cases(self):
        self.assertIsNone(snap_inward(Crop(10, 10, 3, 3), (16, 8), FRAME))
        self.assertIsNone(snap_inward(Crop(100, 100, 1900, 0), (16, 8), FRAME))
        self.assertIsNone(snap_inward(Crop(100, 1200, 0, 0), (16, 8), FRAME))

    def test_crop_rotate_matches_pillow(self):
        out = crop_rotate(self.jpeg, Crop(1168, 1080, 176, 0))
        ref = Image.open(io.BytesIO(self.jpeg)).crop((176, 0, 1344, 1080)).rotate(180)
        got = Image.open(io.BytesIO(out))
        self.assertEqual(got.size, (1168, 1080))
        diff = np.abs(np.asarray(got.convert("RGB"), float) - np.asarray(ref.convert("RGB"), float))
        self.assertLess(diff.mean(), 1.0)

    def test_marker_outside_crop_is_absent(self):
        out = Image.open(io.BytesIO(crop_rotate(self.jpeg, Crop(1168, 1080, 176, 0)))).convert("RGB")
        a = np.asarray(out).astype(int)
        red = (a[..., 0] > 200) & (a[..., 1] < 60) & (a[..., 2] < 60)
        green = (a[..., 1] > 200) & (a[..., 0] < 60) & (a[..., 2] < 60)
        self.assertEqual(int(red.sum()), 0)
        self.assertGreater(int(green.sum()), 1000)

    def test_misaligned_crop_raises(self):
        with self.assertRaises(LosslessError):
            crop_rotate(self.jpeg, Crop(1180, 1080, 164, 0))

    def test_garbage_raises(self):
        with self.assertRaises(LosslessError):
            crop_rotate(b"not a jpeg", Crop(16, 8, 0, 0))

    def test_archive_geometry(self):
        self.assertEqual(archive_geometry(Crop(1168, 1080, 176, 0)), "1168x1080+176+0/rot180")


if __name__ == "__main__":
    unittest.main()
