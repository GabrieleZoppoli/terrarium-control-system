"""timelapse configuration constants (later tasks extend this file)."""
from camgate.config import SURVEIL_CONF  # CROP source of truth: /etc/surveil/surveil.conf

JPEGTRAN = "jpegtran"
JPEGTRAN_TIMEOUT_S = 10

AFTER_PRIVATE_S = 600      # camgate gate must have been ok this long
MIST_QUIET_S = 300         # no mist within this many seconds
NR_GLOBALS = "/home/pi/.node-red/context/global/global.json"
GLOBALS_MAX_AGE_S = 3600   # stale NR globals file => no light window

ARCHIVE_ROOT = "/var/lib/terrarium-timelapse"
CAP_GB = 40
FLOOR_GB = 15
BURST_N = 3
BURST_GAP_S = 0.3
GATE_URL = "http://127.0.0.1:8788/internal/archive-gate.json"
CONDITIONS_URL = "http://127.0.0.1:8787/api/conditions.json"
SNAPSHOT_URL = "http://127.0.0.1:8080/snapshot"
INFLUX_URL = "http://127.0.0.1:8086/query"
INFLUX_DB = "highland"

REGISTRY_PATH = ARCHIVE_ROOT + "/registry.json"
CONFIDENT = 0.8            # vision confidence needed to change an item
PUBLIC_STREAK = 3          # consecutive confident days before unconfirmed goes public

CLAUDE_BIN = "/home/pi/.local/bin/claude"
VISION_TIMEOUT_S = 900
