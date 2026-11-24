"""Live hub: one shared camera reader fanned out to a few short, fail-closed sessions.

The reader thread keeps only the latest raw frame and does no image work.
A frame is cropped lazily, once per (frame, crop), when the first session
takes it, so crop work is bounded by what sessions actually send (at most
LIVE_FPS per session) and is zero for sessions nobody iterates. Each session
re-checks the privacy
decision and the crop before yielding every frame and on every wait timeout,
so a door opening or a stalled camera ends the stream within about 0.5 s.
"""
import logging
import math
import threading
import time
from typing import Callable, Iterator, NamedTuple, Optional

from .camera import CameraError
from .config import LIVE_COOLDOWN_S, LIVE_FPS, LIVE_MAX_VIEWERS, LIVE_SESSION_S
from .frames import crop_jpeg

log = logging.getLogger("camgate.live")

WAIT_S = 0.5  # longest real-time wait before re-checking privacy and deadline
STARTUP_TIMEOUT_S = 5.0


class Busy(Exception):
    def __init__(self, retry_after_s: int):
        super().__init__(f"live viewer cap reached; retry in {retry_after_s}s")
        self.retry_after_s = retry_after_s


class Cooldown(Exception):
    def __init__(self, retry_after_s: int):
        super().__init__(f"visitor in cooldown; retry in {retry_after_s}s")
        self.retry_after_s = retry_after_s


class Private(Exception):
    def __init__(self):
        super().__init__("camera is private")


def _retry_s(seconds: float) -> int:
    try:
        return max(1, math.ceil(seconds))
    except (ValueError, OverflowError):
        return 1


class _Frame(NamedTuple):
    gen: int
    seq: int
    raw: bytes


class Session:
    def __init__(self, hub: "LiveHub", visitor: str, gen: int, started: float):
        self._hub = hub
        self.visitor = visitor
        self._gen = gen
        self.deadline = started + LIVE_SESSION_S
        self._ended = False
        self._failed = False

    def _expired(self) -> bool:
        return not (self._hub._clock() < self.deadline)

    def frames(self) -> Iterator[bytes]:
        hub = self._hub
        cond = hub._cond
        interval = 1.0 / LIVE_FPS
        startup_deadline = time.monotonic() + hub._startup_timeout_s
        last_seq = 0
        last_yield = None
        got_any = False
        sent = 0
        reason = "closed"
        try:
            while True:
                if self._expired():
                    reason = "session_time_up"
                    return
                if hub._allowed_crop() is None:
                    reason = "private"
                    return
                with cond:
                    if self._ended:
                        if self._failed:
                            reason = "camera_failed"
                            if not got_any:
                                raise CameraError("camera stream failed")
                        return
                    now_m = time.monotonic()
                    if last_yield is not None and now_m < last_yield + interval:
                        cond.wait(min(WAIT_S, last_yield + interval - now_m))
                        continue
                    f = hub._frame
                    if f is None or f.gen != self._gen or f.seq <= last_seq:
                        if not got_any:
                            left = startup_deadline - now_m
                            if left <= 0:
                                reason = "startup_timeout"
                                raise CameraError("no camera frame within startup timeout")
                            cond.wait(min(WAIT_S, left))
                        else:
                            cond.wait(WAIT_S)
                        continue
                    last_seq = f.seq
                crop = hub._allowed_crop()
                if crop is None or self._expired():
                    reason = "private_or_time_up"
                    return
                jpeg = hub._cropped(f, crop)
                if jpeg is None:
                    reason = "crop_failed"
                    return  # fail closed
                now_crop = hub._allowed_crop()
                if now_crop is None or self._expired():
                    reason = "private_or_time_up"
                    return
                if now_crop != crop:
                    continue  # crop changed while cropping; never serve a stale crop
                yield jpeg
                got_any = True
                sent += 1
                last_yield = time.monotonic()
        finally:
            log.info("live session ended: %s after %d frames", reason, sent)
            hub._end(self)

    def close(self) -> None:
        self._hub._end(self)


class LiveHub:
    def __init__(
        self,
        source,
        decide_fn: Callable,
        crop_fn: Callable,
        clock: Callable[[], float] = time.time,
        max_viewers: int = LIVE_MAX_VIEWERS,
        startup_timeout_s: float = STARTUP_TIMEOUT_S,
    ):
        self._source = source
        self._decide = decide_fn
        self._crop = crop_fn
        self._clock = clock
        self._max_viewers = max_viewers
        self._startup_timeout_s = startup_timeout_s
        self._cond = threading.Condition()
        self._sessions = set()
        self._cooldowns = {}
        self._gen = 0
        self._seq = 0
        self._frame: Optional[_Frame] = None
        self._crop_lock = threading.Lock()
        self._crop_cache = None  # (gen, seq, crop, jpeg or None)
        self._thread: Optional[threading.Thread] = None
        self._stop: Optional[threading.Event] = None

    # -- privacy -------------------------------------------------------------
    def _allowed_crop(self):
        """The crop to use if pixels may be public right now, else None."""
        try:
            if not self._decide(self._clock()).public:
                return None
            return self._crop()
        except Exception:
            return None

    # -- sessions ------------------------------------------------------------
    def open_session(self, visitor: str) -> Session:
        if self._allowed_crop() is None:
            raise Private()
        with self._cond:
            now = self._clock()
            for s in [s for s in self._sessions if not (now < s.deadline)]:
                self._end_locked(s)
            for v in [v for v, until in self._cooldowns.items() if not (now < until)]:
                del self._cooldowns[v]
            until = self._cooldowns.get(visitor)
            if until is not None:
                raise Cooldown(_retry_s(until - now))
            if len(self._sessions) >= self._max_viewers:
                soonest = min((s.deadline for s in self._sessions), default=now)
                raise Busy(_retry_s(soonest - now))
            if self._stop is None:
                self._start_reader_locked()
            session = Session(self, visitor, self._gen, now)
            self._sessions.add(session)
            return session

    def slots_free(self) -> int:
        with self._cond:
            return max(0, self._max_viewers - len(self._sessions))

    def _end(self, session: Session, failed: bool = False) -> None:
        with self._cond:
            self._end_locked(session, failed)

    def _end_locked(self, session: Session, failed: bool = False) -> None:
        if session._ended:
            return
        session._ended = True
        session._failed = failed
        self._sessions.discard(session)
        self._cooldowns[session.visitor] = self._clock() + LIVE_COOLDOWN_S
        if not self._sessions:
            self._stop_reader_locked()
        self._cond.notify_all()

    def _cropped(self, f: _Frame, crop) -> Optional[bytes]:
        """Crop frame f with crop, once per (frame, crop); None if cropping fails."""
        with self._crop_lock:
            c = self._crop_cache
            if c is not None and c[0] == f.gen and c[1] == f.seq and c[2] == crop:
                return c[3]
            try:
                jpeg = crop_jpeg(f.raw, crop)
            except Exception:
                jpeg = None
            self._crop_cache = (f.gen, f.seq, crop, jpeg)
            return jpeg

    # -- reader --------------------------------------------------------------
    def _start_reader_locked(self) -> None:
        self._gen += 1
        self._frame = None
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._run, args=(self._gen, self._stop), name="camgate-live-reader", daemon=True
        )
        self._thread.start()

    def _stop_reader_locked(self) -> None:
        if self._stop is not None:
            self._stop.set()
        self._stop = None
        self._frame = None
        self._crop_cache = None

    def _run(self, gen: int, stop: threading.Event) -> None:
        it = None
        why = "source ended"
        try:
            it = iter(self._source.frames())
            for raw in it:
                if stop.is_set():
                    return
                with self._cond:
                    if stop.is_set():
                        return
                    self._seq += 1
                    self._frame = _Frame(gen, self._seq, raw)
                    self._cond.notify_all()
        except Exception as e:
            why = f"source raised {e!r}"
        finally:
            if it is not None and hasattr(it, "close"):
                try:
                    it.close()
                except Exception:
                    pass
            if not stop.is_set():
                log.warning("live reader failed (%s); ending its sessions", why)
                self._fail(gen)

    def _fail(self, gen: int) -> None:
        """The source ended or raised: end every session that relied on it."""
        with self._cond:
            if gen != self._gen:
                return
            for s in list(self._sessions):
                if s._gen == gen:
                    self._end_locked(s, failed=True)
            if self._gen == gen:
                self._stop_reader_locked()
