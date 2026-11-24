"""Privacy policy: decides whether camera pixels may be public. Fails closed."""
from typing import NamedTuple, Optional

from .config import DOOR_STALE_S, SERIAL_STALE_S, SHOWME_MAX_S


class DoorSignal(NamedTuple):
    open: Optional[bool]
    serial_age_s: float
    ts: float


class ShowMe(NamedTuple):
    on: bool
    until: Optional[float]


class Decision(NamedTuple):
    public: bool
    reason: str


def _showme_active(now, showme):
    if showme is None or not showme.on or showme.until is None:
        return False
    # Written so NaN compares False and therefore means "not active".
    return showme.until > now and showme.until - now <= SHOWME_MAX_S


showme_active = _showme_active  # public name for status reporting


def decide(now, doors, showme, crop):
    """Return the public/private decision. `crop is None` means invalid CROP."""
    if crop is None:
        return Decision(False, "crop_invalid")
    if _showme_active(now, showme):
        return Decision(True, "showme")
    if doors is None or doors.open is None:
        return Decision(False, "door_state_unknown")
    # Negated "fresh" tests so NaN values fail closed.
    if not (now - doors.ts <= DOOR_STALE_S):
        return Decision(False, "door_signal_stale")
    if not (doors.serial_age_s <= SERIAL_STALE_S):
        return Decision(False, "serial_stale")
    if doors.open:
        return Decision(False, "doors_open")
    return Decision(True, "ok")
