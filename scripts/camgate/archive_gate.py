"""Archive gate: tracks how long the doors have been closed, for the time-lapse job.

Loopback-only (served outside /cam/, so the public proxy never forwards it).
Fails closed: not ok until a fresh "ok" decision has been observed.
"""
import threading
import time

from .policy import Decision

OBSERVATION_MAX_AGE_S = 3.0


class ArchiveGate:
    def __init__(self, clock=time.time):
        self._lock = threading.Lock()
        # The state before start is unknown, so it counts as not ok.
        self._last_not_ok_at = clock()
        self._seen_at = None
        self._reason = "no_observation"

    def observe(self, now: float, decision: Decision) -> None:
        with self._lock:
            self._seen_at = now
            self._reason = decision.reason
            if decision.reason != "ok":
                self._last_not_ok_at = now

    def state(self, now: float) -> dict:
        with self._lock:
            fresh = self._seen_at is not None and 0 <= now - self._seen_at <= OBSERVATION_MAX_AGE_S
            reason = self._reason if fresh else (self._reason if self._seen_at is None else "stale")
            return {
                "ok": bool(fresh and self._reason == "ok"),
                "reason": reason,
                "last_not_ok_at": self._last_not_ok_at,
                "now": now,
            }
