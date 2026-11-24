"""timelapse configuration constants (later tasks extend this file)."""
from camgate.config import SURVEIL_CONF  # CROP source of truth: /etc/surveil/surveil.conf

JPEGTRAN = "jpegtran"
JPEGTRAN_TIMEOUT_S = 10

AFTER_PRIVATE_S = 600      # camgate gate must have been ok this long
MIST_QUIET_S = 300         # no mist within this many seconds
NR_GLOBALS = "/home/pi/.node-red/context/global/global.json"
GLOBALS_MAX_AGE_S = 3600   # stale NR globals file => no light window
