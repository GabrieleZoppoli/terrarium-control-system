"""Camera sources (ustreamer on loopback) and the cropped-still keeper."""
import threading
import time
import urllib.request
from typing import Callable, Iterator, Optional

from .config import STILL_REFRESH_S, USTREAMER_SNAPSHOT, USTREAMER_STREAM
from .frames import blur_jpeg, crop_jpeg, iter_mjpeg_frames, placeholder_jpeg

TIMEOUT_S = 5


class CameraError(Exception):
    """The camera could not deliver a frame."""


class SnapshotSource:
    def fetch(self) -> bytes:
        try:
            with urllib.request.urlopen(USTREAMER_SNAPSHOT, timeout=TIMEOUT_S) as r:
                data = r.read()
        except Exception as e:
            raise CameraError(f"snapshot failed: {e}") from e
        if not data:
            raise CameraError("snapshot empty")
        return data


class StreamSource:
    def frames(self) -> Iterator[bytes]:
        try:
            with urllib.request.urlopen(USTREAMER_STREAM, timeout=TIMEOUT_S) as r:
                yield from iter_mjpeg_frames(r)
        except Exception as e:
            raise CameraError(f"stream failed: {e}") from e


class StillKeeper:
    """Holds the last already-cropped still; the blur is derived from it.

    A still is "suspect" once any private decision has been seen after it was
    taken: it may have been captured during door-signal latency and show the
    gardener. A suspect still is only ever served blurred, even while public,
    until a still captured after the private period replaces it; seeing a
    private decision also makes the next capture due at once.
    """

    def __init__(self, source, decide_fn: Callable, crop_fn: Callable, clock=time.time):
        self._source = source
        self._decide = decide_fn
        self._crop = crop_fn
        self._clock = clock
        self._lock = threading.Lock()
        self._next_due = float("-inf")
        self._still: Optional[bytes] = None
        self._blurred: Optional[bytes] = None
        self._taken_at: Optional[float] = None
        self._suspect = False
        self._private_seen = 0  # bumped on every private decision observed

    def _saw_private_locked(self) -> None:
        self._suspect = True
        self._private_seen += 1
        self._next_due = float("-inf")

    def _saw_private(self) -> None:
        with self._lock:
            self._saw_private_locked()

    def tick(self) -> None:
        start = self._clock()
        if not self._decide(start).public:
            self._saw_private()
            return
        with self._lock:
            if start < self._next_due:
                return
            seen = self._private_seen
        try:
            frame = self._source.fetch()
        except Exception:
            return
        if not self._decide(self._clock()).public:
            self._saw_private()
            return
        crop = self._crop()
        if crop is None:
            return
        try:
            cropped = crop_jpeg(frame, crop)
        except Exception:
            return
        with self._lock:
            if self._private_seen != seen:
                return  # a private decision was seen during the fetch; retry next tick
            self._still = cropped
            self._blurred = None
            self._taken_at = start
            self._suspect = False
            self._next_due = start + STILL_REFRESH_S

    def taken_at(self) -> Optional[float]:
        """Epoch of the held still, without computing any blur."""
        with self._lock:
            return self._taken_at

    def current(self):
        public = self._decide(self._clock()).public
        with self._lock:
            if not public:
                self._saw_private_locked()
            if self._still is None:
                return placeholder_jpeg(), None
            if public and not self._suspect:
                return self._still, self._taken_at
            if self._blurred is None:
                self._blurred = blur_jpeg(self._still)
            return self._blurred, self._taken_at
