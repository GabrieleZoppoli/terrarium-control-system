import io
import unittest

from PIL import Image

from camgate.config import NO_CROP, Crop
from camgate.frames import blur_jpeg, crop_jpeg, iter_mjpeg_frames, placeholder_jpeg


def jpeg_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def make_frame():
    """1920x1080 synthetic frame: left 1344 px noisy-ish blue, right 576 px pure red."""
    img = Image.new("RGB", (1920, 1080), (0, 0, 255))
    for x in range(0, 1344, 16):
        for y in range(0, 1080, 16):
            if (x // 16 + y // 16) % 2:
                img.paste((255, 255, 255), (x, y, x + 16, y + 16))
    img.paste((255, 0, 0), (1344, 0, 1920, 1080))
    return jpeg_bytes(img)


def part(j):
    return (b"--boundarydonotcross\r\nContent-Type: image/jpeg\r\n"
            b"Content-Length: %d\r\n\r\n" % len(j)) + j + b"\r\n"


def variance(img):
    px = list(img.convert("L").getdata())
    m = sum(px) / len(px)
    return sum((p - m) ** 2 for p in px) / len(px)


class FrameTests(unittest.TestCase):
    def test_crop_dimensions_and_removes_right_side(self):
        out = Image.open(io.BytesIO(crop_jpeg(make_frame(), Crop(1344, 1080, 0, 0)))).convert("RGB")
        self.assertEqual(out.size, (1344, 1080))
        r, g, b = out.getpixel((1340, 540))
        self.assertFalse(r > 200 and g < 100 and b < 100)

    def test_output_is_rotated_180_after_crop(self):
        # Crop straddles the blue/red edge: red is on the right of the raw crop,
        # so after a 180 degree turn it must be on the left.
        out = Image.open(io.BytesIO(crop_jpeg(make_frame(), Crop(400, 200, 1144, 0)))).convert("RGB")
        self.assertEqual(out.size, (400, 200))
        r, g, b = out.getpixel((50, 100))
        self.assertTrue(r > 200 and g < 100 and b < 100)
        r, g, b = out.getpixel((350, 100))
        self.assertFalse(r > 200 and g < 100 and b < 100)

    def test_crop_offset(self):
        out = Image.open(io.BytesIO(crop_jpeg(make_frame(), Crop(500, 400, 1400, 100)))).convert("RGB")
        self.assertEqual(out.size, (500, 400))
        r, g, b = out.getpixel((250, 200))
        self.assertTrue(r > 200 and g < 100 and b < 100)

    def test_no_crop_keeps_full_frame(self):
        self.assertEqual(Image.open(io.BytesIO(crop_jpeg(make_frame(), NO_CROP))).size, (1920, 1080))

    def test_crop_none_raises(self):
        self.assertRaises(ValueError, crop_jpeg, make_frame(), None)

    def test_crop_larger_than_frame_raises(self):
        self.assertRaises(ValueError, crop_jpeg, make_frame(), Crop(2000, 1080, 0, 0))

    def test_blur_keeps_size_and_lowers_variance(self):
        src = make_frame()
        out = Image.open(io.BytesIO(blur_jpeg(src)))
        self.assertEqual(out.size, (1920, 1080))
        self.assertLess(variance(out), variance(Image.open(io.BytesIO(src))) / 2)

    def test_placeholder_is_jpeg(self):
        data = placeholder_jpeg()
        self.assertEqual(data[:2], b"\xff\xd8")
        self.assertEqual(Image.open(io.BytesIO(data)).size, (1344, 1080))

    def test_iter_mjpeg_frames_splits_parts(self):
        js = [jpeg_bytes(Image.new("RGB", (8 + i, 8), (i * 40, 0, 0))) for i in range(3)]
        body = b"".join(part(j) for j in js)
        self.assertEqual(list(iter_mjpeg_frames(io.BytesIO(body))), js)

    def test_iter_mjpeg_frames_ignores_boundary_string(self):
        j = jpeg_bytes(Image.new("RGB", (8, 8)))
        body = part(j).replace(b"boundarydonotcross", b"whatever")
        self.assertEqual(list(iter_mjpeg_frames(io.BytesIO(body))), [j])

    def test_iter_mjpeg_frames_stops_on_truncated_part(self):
        j1 = jpeg_bytes(Image.new("RGB", (8, 8)))
        j2 = jpeg_bytes(Image.new("RGB", (9, 9)))
        body = part(j1) + part(j2)[:-20]
        self.assertEqual(list(iter_mjpeg_frames(io.BytesIO(body))), [j1])

    def test_iter_mjpeg_frames_empty_stream(self):
        self.assertEqual(list(iter_mjpeg_frames(io.BytesIO(b""))), [])


if __name__ == "__main__":
    unittest.main()
