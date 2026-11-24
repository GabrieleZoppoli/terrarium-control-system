"""JPEG frame operations: crop, blur, placeholder, MJPEG part splitting."""
import io
from typing import BinaryIO, Iterator

from PIL import Image, ImageDraw, ImageFilter

from .config import BLUR_RADIUS, JPEG_QUALITY, NO_CROP, Crop


def _encode(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=JPEG_QUALITY)
    return buf.getvalue()


def crop_jpeg(jpeg: bytes, crop) -> bytes:
    """Crop a JPEG. Raises ValueError unless crop is a Crop or NO_CROP."""
    if crop is NO_CROP:
        box = None
    elif isinstance(crop, Crop):
        box = (crop.x, crop.y, crop.x + crop.w, crop.y + crop.h)
    else:
        raise ValueError("no valid crop decision; refusing to emit pixels")
    with Image.open(io.BytesIO(jpeg)) as img:
        img.load()
        if box is not None:
            if box[2] > img.width or box[3] > img.height:
                raise ValueError("crop exceeds frame size")
            img = img.crop(box)
        return _encode(img)


def blur_jpeg(jpeg: bytes) -> bytes:
    with Image.open(io.BytesIO(jpeg)) as img:
        img.load()
        return _encode(img.filter(ImageFilter.GaussianBlur(BLUR_RADIUS)))


def placeholder_jpeg(w: int = 1344, h: int = 1080) -> bytes:
    img = Image.new("RGB", (w, h), (24, 28, 26))
    d = ImageDraw.Draw(img)
    msg = "camera private"
    tw = d.textlength(msg)
    d.text(((w - tw) / 2, h / 2), msg, fill=(200, 205, 200))
    return _encode(img)


def iter_mjpeg_frames(stream: BinaryIO) -> Iterator[bytes]:
    """Yield JPEG bodies from a multipart stream using per-part Content-Length.

    Stops at EOF or on a truncated/malformed part (truncated part not yielded).
    """
    while True:
        length = None
        saw_header = False
        while True:
            line = stream.readline()
            if not line:
                return
            line = line.strip()
            if not line:
                if saw_header and length is not None:
                    break
                if saw_header:
                    return  # headers ended without Content-Length
                continue  # blank line between parts
            if line.startswith(b"--"):
                saw_header = False
                length = None
                continue
            saw_header = True
            name, _, val = line.partition(b":")
            if name.strip().lower() == b"content-length":
                try:
                    length = int(val.strip())
                except ValueError:
                    return
        if length <= 0:
            return
        body = stream.read(length)
        if len(body) < length:
            return
        yield body
