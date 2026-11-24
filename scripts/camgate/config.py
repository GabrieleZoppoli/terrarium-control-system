"""camgate configuration constants and the CROP loader (fails closed)."""
from typing import NamedTuple, Optional, Union

PORT = 8788
SURVEIL_CONF = "/etc/surveil/surveil.conf"
USTREAMER_SNAPSHOT = "http://127.0.0.1:8080/snapshot"
USTREAMER_STREAM = "http://127.0.0.1:8080/stream"
MQTT_HOST = "localhost"
MQTT_PORT = 1883
TOPIC_DOORS = "terrarium/camera/doors"
TOPIC_SHOWME = "terrarium/camera/showme"
DOOR_STALE_S = 3.0
SERIAL_STALE_S = 10.0
SHOWME_MAX_S = 1800
LIVE_SESSION_S = 1800   # owner 2026-11-24: stay live until a door opens; 30 min backstop for forgotten tabs
LIVE_FPS = 3
LIVE_MAX_VIEWERS = 3
LIVE_COOLDOWN_S = 5
STILL_REFRESH_S = 180
JPEG_QUALITY = 85
BLUR_RADIUS = 24


class Crop(NamedTuple):
    w: int
    h: int
    x: int
    y: int


class _NoCrop:
    """Sentinel: CROP=none was set explicitly, full frame allowed."""

    def __repr__(self):
        return "NO_CROP"


NO_CROP = _NoCrop()


def load_crop(path: str) -> Union[Crop, _NoCrop, None]:
    """Return Crop, NO_CROP (explicit CROP=none), or None (missing/invalid -> private)."""
    try:
        value = None
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                if key.strip() == "CROP":
                    value = val.strip().strip("\"'")
        if value is None:
            return None
        if value == "none":
            return NO_CROP
        parts = value.split(":")
        if len(parts) != 4:
            return None
        w, h, x, y = (int(p) for p in parts)
        if w <= 0 or h <= 0 or x < 0 or y < 0:
            return None
        return Crop(w, h, x, y)
    except Exception:
        return None
