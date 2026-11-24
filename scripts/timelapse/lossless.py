"""Lossless privacy crop + 180 degree rotate of camera JPEGs via jpegtran.

The crop is snapped INWARD to the JPEG MCU grid so no pixel outside the
privacy region is ever stored. Any mismatch raises; it never expands.
"""
import io
import subprocess
from typing import Optional, Tuple

from PIL import Image

from camgate.config import Crop

from .config import JPEGTRAN, JPEGTRAN_TIMEOUT_S


class LosslessError(Exception):
    """jpegtran failed or produced a region different from the requested one."""


def mcu_size(jpeg: bytes) -> Tuple[int, int]:
    """MCU size in pixels: (8 * max h-sampling, 8 * max v-sampling)."""
    with Image.open(io.BytesIO(jpeg)) as im:
        layers = im.layer
    return 8 * max(l[1] for l in layers), 8 * max(l[2] for l in layers)


def snap_inward(crop: Crop, mcu: Tuple[int, int], frame: Tuple[int, int]) -> Optional[Crop]:
    """Shrink crop to the MCU grid (start rounded up, end rounded down).

    The end may stay at the frame edge even if that is off-grid. Returns None
    if the crop is outside the frame or nothing is left.
    """
    mw, mh = mcu
    fw, fh = frame
    if crop.x < 0 or crop.y < 0 or crop.w <= 0 or crop.h <= 0:
        return None
    if crop.x + crop.w > fw or crop.y + crop.h > fh:
        return None
    x0 = -(-crop.x // mw) * mw
    y0 = -(-crop.y // mh) * mh
    x1, y1 = crop.x + crop.w, crop.y + crop.h
    if x1 != fw:
        x1 = x1 // mw * mw
    if y1 != fh:
        y1 = y1 // mh * mh
    if x1 <= x0 or y1 <= y0:
        return None
    return Crop(x1 - x0, y1 - y0, x0, y0)


def _run(args, data: bytes) -> bytes:
    try:
        p = subprocess.run([JPEGTRAN, "-copy", "none", "-perfect"] + args, input=data,
                           capture_output=True, timeout=JPEGTRAN_TIMEOUT_S)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise LosslessError("jpegtran did not run: %s" % e)
    if p.returncode != 0 or not p.stdout:
        raise LosslessError("jpegtran failed rc=%d: %s" % (p.returncode, p.stderr[:200]))
    return p.stdout


def crop_rotate(jpeg: bytes, crop: Crop) -> bytes:
    """Losslessly crop then rotate 180. Raises LosslessError unless the
    output is exactly crop.w x crop.h (jpegtran silently enlarges misaligned crops)."""
    out = _run(["-crop", "%dx%d+%d+%d" % (crop.w, crop.h, crop.x, crop.y)], jpeg)
    out = _run(["-rotate", "180"], out)
    try:
        with Image.open(io.BytesIO(out)) as im:
            size = im.size
    except Exception as e:
        raise LosslessError("unreadable jpegtran output: %s" % e)
    if size != (crop.w, crop.h):
        raise LosslessError("output %r != requested %r" % (size, (crop.w, crop.h)))
    return out


def archive_geometry(crop: Crop) -> str:
    """Geometry tag recorded with archived frames, e.g. 1168x1080+176+0/rot180."""
    return "%dx%d+%d+%d/rot180" % (crop.w, crop.h, crop.x, crop.y)
