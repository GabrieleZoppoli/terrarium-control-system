import io
import unittest

from PIL import Image

from timelapse import annotate


def _jpeg(w=400, h=300, color=(40, 90, 40)):
    b = io.BytesIO()
    Image.new("RGB", (w, h), color).save(b, "JPEG", quality=95)
    return b.getvalue()


class TestDots(unittest.TestCase):
    def test_same_size_and_white_centre(self):
        out = annotate.draw_dots(_jpeg(), [{"id": "3", "x": 100, "y": 100}])
        im = Image.open(io.BytesIO(out))
        self.assertEqual(im.size, (400, 300))
        r, g, b = im.convert("RGB").getpixel((100, 100))
        self.assertTrue(min(r, g, b) > 230)

    def test_pending_orange_ring(self):
        out = annotate.draw_dots(_jpeg(), [{"id": "3", "x": 100, "y": 100, "needs_owner": True}])
        im = Image.open(io.BytesIO(out)).convert("RGB")
        r, g, b = im.getpixel((100 + 8, 100))
        self.assertTrue(r > 200 and g > 100 and b < 120)

    def test_out_of_frame_ok(self):
        annotate.draw_dots(_jpeg(), [{"id": "1", "x": -5, "y": 9999}])


if __name__ == "__main__":
    unittest.main()
