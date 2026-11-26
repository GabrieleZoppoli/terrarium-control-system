"""Flower markers for the website overlay, served as /cam/flowers.json.

The time-lapse writes the file (trusted flowers only, public-frame pixels).
Here it is only checked: anything odd, or made for another crop, gives no
markers rather than markers in the wrong place.
"""
import json

from .config import Crop

STATES = ("bud", "opening", "open", "fading")
MAX_BYTES = 64 * 1024
MAX_ITEMS = 50


def _empty():
    return {"w": 0, "h": 0, "items": []}


def _int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def load(path, crop) -> dict:
    """{"w", "h", "items": [{"num", "state", "x", "y"}]} for the live crop, or no items."""
    if not isinstance(crop, Crop):
        return _empty()
    try:
        with open(path, "rb") as f:
            raw = f.read(MAX_BYTES + 1)
        doc = json.loads(raw) if len(raw) <= MAX_BYTES else None
    except (OSError, ValueError):
        return _empty()
    if not isinstance(doc, dict) or doc.get("crop") != "%d:%d:%d:%d" % crop:
        return _empty()
    items = []
    for it in doc.get("items") or []:
        if not isinstance(it, dict):
            continue
        num, state, x, y = it.get("num"), it.get("state"), it.get("x"), it.get("y")
        if (_int(num) and 1 <= num <= 999 and state in STATES and _int(x) and _int(y)
                and 0 <= x < crop.w and 0 <= y < crop.h):
            items.append({"num": num, "state": state, "x": x, "y": y})
    return {"w": crop.w, "h": crop.h, "items": items[:MAX_ITEMS]}
