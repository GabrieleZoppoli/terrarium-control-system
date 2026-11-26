"""Public flower list for the website overlay.

Only trusted items (registry.is_public) that are still visible, with
coordinates moved from the archive frame into the public camera frame.
camgate serves this file at /cam/flowers.json and drops it if the crop it
was made for is no longer the live crop.
"""
import json
import re
from pathlib import Path
from typing import Optional

from camgate.config import Crop, load_crop

from . import config, storage

SHOWN_STATES = ("bud", "opening", "open", "fading")
_GEO = re.compile(r"^(\d+)x(\d+)\+(\d+)\+(\d+)/rot180$")


def parse_geometry(geo: str) -> Optional[Crop]:
    """'1168x1080+176+0/rot180' -> Crop(w, h, x, y); None if not that shape."""
    m = _GEO.match(geo or "")
    return Crop(*(int(g) for g in m.groups())) if m else None


def to_public_xy(x, y, archive: Crop, public: Crop):
    """Archive pixel -> public pixel. Both frames are camera crops rotated 180 degrees."""
    raw_x = archive.x + (archive.w - 1 - x)
    raw_y = archive.y + (archive.h - 1 - y)
    return (public.w - 1) - (raw_x - public.x), (public.h - 1) - (raw_y - public.y)


def crop_tag(crop: Crop) -> str:
    return "%d:%d:%d:%d" % (crop.w, crop.h, crop.x, crop.y)


def build(reg: dict, public: Optional[Crop]) -> dict:
    """The public document. No usable crop or geometry -> no items."""
    from .registry import is_public  # registry imports this module

    archive = parse_geometry(reg.get("geometry", ""))
    if not isinstance(public, Crop) or archive is None:
        return {"crop": "", "w": 0, "h": 0, "items": []}
    items = []
    for iid, it in sorted((reg.get("items") or {}).items()):
        if not (isinstance(it, dict) and is_public(it) and it.get("state") in SHOWN_STATES):
            continue
        m = re.fullmatch(r"f(\d+)", iid)
        if not m:
            continue
        px, py = to_public_xy(it["x"], it["y"], archive, public)
        if 0 <= px < public.w and 0 <= py < public.h:
            items.append({"num": int(m.group(1)), "state": it["state"], "x": px, "y": py})
    return {"crop": crop_tag(public), "w": public.w, "h": public.h, "items": items}


def write(registry_path, reg: dict, crop_path=None) -> None:
    """Write public-flowers.json next to the registry; on any failure remove it (fail closed)."""
    out = Path(registry_path).parent / config.PUBLIC_FLOWERS_NAME
    try:
        doc = build(reg, load_crop(crop_path or config.SURVEIL_CONF))
        storage.write_atomic(out, (json.dumps(doc, sort_keys=True) + "\n").encode())
    except Exception:
        try:
            out.unlink()
        except OSError:
            pass
        raise
