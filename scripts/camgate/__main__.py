"""camgate entry point: python3 -m camgate (run from scripts/)."""
import datetime
import logging
import os
import threading
import time

from .camera import SnapshotSource, StillKeeper, StreamSource
from .config import LIVE_MAX_VIEWERS, PORT, SURVEIL_CONF, load_crop
from .live import LiveHub
from .policy import decide, showme_active
from .server import make_server
from .signals import SignalStore, start_mqtt

log = logging.getLogger("camgate")

CROP_TTL_S = 10.0
TICK_S = 5.0


def make_cached_crop_fn(conf_path, ttl=CROP_TTL_S, clock=time.monotonic, loader=load_crop):
    """crop_fn that re-reads the conf at most every `ttl` s; an exception gives None."""
    lock = threading.Lock()
    state = {"at": None, "val": None}

    def crop_fn():
        with lock:
            now = clock()
            if state["at"] is None or now - state["at"] >= ttl:
                try:
                    state["val"] = loader(conf_path)
                except Exception:
                    log.exception("crop load failed")
                    state["val"] = None
                state["at"] = now
            return state["val"]

    return crop_fn


def make_status_fn(store, keeper, hub, crop_fn, clock=time.time):
    def status_fn():
        now = clock()
        doors, showme = store.snapshot()
        d = decide(now, doors, showme, crop_fn())
        taken = keeper.taken_at()
        return {
            "public": d.public,
            "reason": d.reason,
            "showme": showme_active(now, showme),
            "live_slots_free": hub.slots_free(),
            "still_taken_at": None
            if taken is None
            else datetime.datetime.fromtimestamp(taken, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    return status_fn


def tick_loop(keeper, interval=TICK_S, stop=None):
    stop = stop or threading.Event()
    while not stop.is_set():
        try:
            keeper.tick()
        except Exception:
            log.exception("keeper.tick failed")
        stop.wait(interval)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    conf = os.environ.get("CAMGATE_SURVEIL_CONF", SURVEIL_CONF)
    port = int(os.environ.get("CAMGATE_PORT", PORT))
    max_viewers = int(os.environ.get("CAMGATE_MAX_VIEWERS", LIVE_MAX_VIEWERS))

    store = SignalStore()
    start_mqtt(store)
    crop_fn = make_cached_crop_fn(conf)
    decide_fn = lambda now: decide(now, *store.snapshot(), crop_fn())
    keeper = StillKeeper(SnapshotSource(), decide_fn, crop_fn)
    hub = LiveHub(StreamSource(), decide_fn, crop_fn, max_viewers=max_viewers)
    threading.Thread(target=tick_loop, args=(keeper,), name="camgate-tick", daemon=True).start()
    srv = make_server(keeper, hub, make_status_fn(store, keeper, hub, crop_fn), port=port)
    log.info("camgate listening on 127.0.0.1:%d", port)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
