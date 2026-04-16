#!/usr/bin/env python3
"""Meross MSS310 persistent daemon.

Maintains a single authenticated session to the Meross cloud API.
Publishes power readings to MQTT every POLL_INTERVAL seconds.
Accepts on/off commands via MQTT.

This replaces the earlier meross_script.py approach, which spawned a new
process every 120 seconds with a full login/discover/logout cycle.
The persistent session reduces API overhead by ~60x and enables 2-second
update resolution on the dashboard.

MQTT topics:
  meross/power/watts    - power reading (float, published every 2s)
  meross/power/command  - "on" or "off" (subscribed)
  meross/power/status   - "online"/"offline" (published, retained)

Usage:
  1. Set environment variables or edit credentials below
  2. Install: sudo cp meross-daemon.service /etc/systemd/system/
  3. Enable: sudo systemctl enable --now meross-daemon
  4. Verify: mosquitto_sub -t meross/power/watts -C 3
"""

import asyncio
import logging
import os
import signal

import paho.mqtt.client as mqtt
from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager

# --- Configuration ---
# Set these directly or use environment variables
EMAIL = os.environ.get("MEROSS_EMAIL", "your_email@example.com")
PASSWORD = os.environ.get("MEROSS_PASSWORD", "your_password")
PLUG_NAME = os.environ.get("MEROSS_PLUG_ID", "your_plug_name")
API_BASE_URL = "https://iotx-eu.meross.com"

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_WATTS = "meross/power/watts"
TOPIC_COMMAND = "meross/power/command"
TOPIC_STATUS = "meross/power/status"

POLL_INTERVAL = 2  # seconds between energy readings
RECONNECT_DELAY = 60  # seconds to wait before reconnecting on failure

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("meross_daemon")

# Suppress noisy meross library logging
for name in ("meross_iot", "meross_iot.manager", "meross_iot.controller",
             "meross_iot.http_api", "meross_iot.device_factory"):
    logging.getLogger(name).setLevel(logging.WARNING)

# Global command queue
_command_queue = asyncio.Queue()


# --- MQTT callbacks (run in paho thread) ---

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        log.info("MQTT connected")
        client.subscribe(TOPIC_COMMAND)
        client.publish(TOPIC_STATUS, "online", retain=True)
    else:
        log.error("MQTT connect failed: rc=%d", rc)


def on_message(client, userdata, msg):
    payload = msg.payload.decode().strip().lower()
    if payload in ("on", "off"):
        _command_queue.put_nowait(payload)
        log.info("Received command: %s", payload)
    else:
        log.warning("Unknown command: %s", payload)


def make_mqtt_client():
    # Use PID in client_id to avoid broker conflicts with stale sessions
    client = mqtt.Client(
        client_id=f"meross_daemon_{os.getpid()}",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )
    client.will_set(TOPIC_STATUS, "offline", retain=True)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start()
    return client


# --- Main async loop ---

async def run(mqtt_client):
    manager = None
    http_client = None

    try:
        log.info("Logging in to Meross cloud...")
        http_client = await MerossHttpClient.async_from_user_password(
            email=EMAIL, password=PASSWORD, api_base_url=API_BASE_URL
        )
        manager = MerossManager(http_client=http_client)
        await manager.async_init()
        await manager.async_device_discovery()

        plug = next(
            (d for d in manager.find_devices() if d.name == PLUG_NAME), None
        )
        if plug is None:
            log.error("Plug '%s' not found", PLUG_NAME)
            return False

        await plug.async_update()
        log.info("Connected to plug '%s'", PLUG_NAME)

        while True:
            # --- Process any pending commands ---
            while not _command_queue.empty():
                cmd = _command_queue.get_nowait()
                try:
                    if cmd == "on":
                        await plug.async_turn_on(channel=0)
                        log.info("Plug turned ON")
                    elif cmd == "off":
                        await plug.async_turn_off(channel=0)
                        log.info("Plug turned OFF")
                except Exception as e:
                    log.error("Command '%s' failed: %s", cmd, e)
                    return False  # trigger reconnect

            # --- Poll energy ---
            try:
                if hasattr(plug, "async_get_instant_metrics"):
                    metrics = await plug.async_get_instant_metrics()
                    watts = metrics.power
                    mqtt_client.publish(TOPIC_WATTS, str(watts))
                    log.info("Power: %.1f W", watts)
                else:
                    log.warning("Plug does not support energy reading")
            except Exception as e:
                log.error("Energy poll failed: %s", e)
                return False  # trigger reconnect

            await asyncio.sleep(POLL_INTERVAL)

    except Exception as e:
        log.error("Session error: %s", e)
        return False
    finally:
        if manager:
            manager.close()
        if http_client:
            try:
                await http_client.async_logout()
            except Exception:
                pass


async def main():
    mqtt_client = make_mqtt_client()
    loop = asyncio.get_event_loop()

    stop_event = asyncio.Event()

    def handle_signal():
        log.info("Shutting down...")
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, handle_signal)

    try:
        while not stop_event.is_set():
            success = await run(mqtt_client)
            if stop_event.is_set():
                break
            if not success:
                log.info("Reconnecting in %ds...", RECONNECT_DELAY)
                try:
                    await asyncio.wait_for(
                        stop_event.wait(), timeout=RECONNECT_DELAY
                    )
                    break  # stop_event was set
                except asyncio.TimeoutError:
                    pass  # reconnect delay elapsed, retry
    finally:
        mqtt_client.publish(TOPIC_STATUS, "offline", retain=True)
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        log.info("Exited cleanly")


if __name__ == "__main__":
    asyncio.run(main())
