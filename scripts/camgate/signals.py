"""Door / show-me signal store and MQTT bridge. Fails closed: any doubt -> None."""
import json
import math
import threading
from typing import Optional, Tuple

import paho.mqtt.client as mqtt

from .config import MQTT_HOST, MQTT_PORT, TOPIC_DOORS, TOPIC_SHOWME
from .policy import DoorSignal, ShowMe


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _load_obj(payload) -> Optional[dict]:
    try:
        obj = json.loads(payload)
    except Exception:
        return None
    return obj if isinstance(obj, dict) else None


def parse_doors(payload: bytes) -> Optional[DoorSignal]:
    obj = _load_obj(payload)
    if obj is None:
        return None
    op = obj.get("open", "missing")
    if op is not None and not isinstance(op, bool):
        return None
    age, ts = obj.get("serial_age_s"), obj.get("ts")
    if not (_is_num(age) and _is_num(ts)):
        return None
    return DoorSignal(op, age, ts)


def parse_showme(payload: bytes) -> Optional[ShowMe]:
    obj = _load_obj(payload)
    if obj is None:
        return None
    on, until, ts = obj.get("on"), obj.get("until"), obj.get("ts")
    if not isinstance(on, bool):
        return None
    if until is not None and not _is_num(until):
        return None
    if not _is_num(ts):
        return None
    return ShowMe(on, until)


class SignalStore:
    """Thread-safe latest signals. Starts disconnected (private) until first connect."""

    def __init__(self):
        self._lock = threading.Lock()
        self._doors: Optional[DoorSignal] = None
        self._showme: Optional[ShowMe] = None
        self._connected = False

    def set_doors(self, sig: Optional[DoorSignal]) -> None:
        with self._lock:
            self._doors = sig

    def set_showme(self, sm: Optional[ShowMe]) -> None:
        with self._lock:
            self._showme = sm

    def set_connected(self, connected: bool) -> None:
        with self._lock:
            self._connected = bool(connected)

    def snapshot(self) -> Tuple[Optional[DoorSignal], Optional[ShowMe]]:
        with self._lock:
            if not self._connected:
                return None, None
            return self._doors, self._showme

    # paho VERSION2 callbacks, bound to the store so they are testable without a broker.
    def on_connect(self, client, userdata, flags, reason_code, properties=None) -> None:
        failed = getattr(reason_code, "is_failure", None)
        if failed is None:
            failed = reason_code != 0
        if failed:
            self.set_connected(False)
            return
        # Subscribe first, connect flag after: retained messages arrive via on_message.
        client.subscribe([(TOPIC_DOORS, 1), (TOPIC_SHOWME, 1)])
        self.set_connected(True)

    def on_disconnect(self, client, userdata, flags=None, reason_code=None, properties=None) -> None:
        self.set_connected(False)

    def on_message(self, client, userdata, msg) -> None:
        try:
            if msg.topic == TOPIC_DOORS:
                self.set_doors(parse_doors(msg.payload))
            elif msg.topic == TOPIC_SHOWME:
                self.set_showme(parse_showme(msg.payload))
        except Exception:
            # Fail closed on anything unexpected.
            if getattr(msg, "topic", None) == TOPIC_DOORS:
                self.set_doors(None)
            elif getattr(msg, "topic", None) == TOPIC_SHOWME:
                self.set_showme(None)


def start_mqtt(store: SignalStore) -> "mqtt.Client":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="camgate")
    client.on_connect = store.on_connect
    client.on_disconnect = store.on_disconnect
    client.on_message = store.on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    client.connect_async(MQTT_HOST, MQTT_PORT, keepalive=30)
    client.loop_start()
    return client
