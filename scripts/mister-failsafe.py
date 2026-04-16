#!/usr/bin/env python3
"""Mister Tapo failsafe — independent of Node-RED.

Queries the mister Tapo P100 plug. If it has been ON for longer than
MAX_ON_SECONDS, forces it OFF and logs the event.

Run via cron every minute:  * * * * * /usr/local/bin/mister-failsafe.py

The plug's own on_time counter is used, so no external state files are needed.
"""

import os
import sys
import time
import signal

IP = os.environ.get("MISTER_PLUG_IP", "192.168.1.199")
EMAIL = os.environ.get("TAPO_EMAIL", "your_email@example.com")
PASSWORD = os.environ.get("TAPO_PASSWORD", "your_password")
MAX_ON_SECONDS = 150  # 2.5 min — longest normal cycle is 90s
LOG_FILE = "/var/log/mister-failsafe.log"
TIMEOUT = 15  # seconds — abort if Tapo API hangs

if EMAIL == "your_email@example.com" or PASSWORD == "your_password":
    print("ERROR: Set TAPO_EMAIL and TAPO_PASSWORD env vars "
          "(e.g. via /etc/terrarium.env loaded by systemd or cron)", file=sys.stderr)
    sys.exit(2)


def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{ts} {msg}\n")


def timeout_handler(signum, frame):
    log("ERROR: Script timed out after {}s".format(TIMEOUT))
    sys.exit(1)


signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(TIMEOUT)

try:
    from PyP100 import PyP100

    plug = PyP100.P100(IP, EMAIL, PASSWORD)
    plug.handshake()
    plug.login()
    info = plug.getDeviceInfo()

    device_on = info.get("device_on", False)
    on_time = info.get("on_time", 0)

    if device_on and on_time > MAX_ON_SECONDS:
        plug.turnOff()
        log("FAILSAFE: Mister was ON for {}s (>{}) — forced OFF".format(
            on_time, MAX_ON_SECONDS))

except Exception as e:
    log("ERROR: {}".format(e))
    sys.exit(1)
