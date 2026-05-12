"""Fetch the Pi ledger endpoint and write ``website/data/ledger.json``.

Run before ``hugo`` to keep the homepage ledger values current. Falls back
to the previous file on fetch failure (Pi outages don't break deploys).
Idempotent; committing the resulting file is normal.
"""
from __future__ import annotations

import json
import re
import ssl
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

URL = "https://rei1.tail7cc014.ts.net/api/ledger.json"
OUT = Path(__file__).resolve().parents[1] / "data/ledger.json"
TIMEOUT_S = 10
REQUIRED_KEYS = ("since", "as_of", "mist_cycles", "electricity",
                 "cost_eur", "co2_scrubbed", "data_points", "fog_hours")
DAYS_PER_MONTH = 30.4375

# `since` is the first sample of ANY measurement in InfluxDB (currently
# 2026-02-04). Power_consumption only exists from the Meross daemon's
# deployment date (2026-02-18 in the current run), so the kWh integral
# covers a shorter window than `since→as_of`. Dividing by the full
# `since→as_of` window under-estimates kWh/day (2.24 instead of the
# correct 2.63). Pi-Claude documented the daemon-start date inside
# `electricity.source`; we parse it out here. If Pi side later exposes
# `electricity.window_start` as a structured field, we use that instead.
_DAEMON_DATE_RE = re.compile(r"daemon came up (\d{4}-\d{2}-\d{2})")


def _iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _electricity_window_start(data: dict) -> datetime:
    elec = data.get("electricity", {})
    explicit = elec.get("window_start")
    if explicit:
        return _iso(explicit)
    m = _DAEMON_DATE_RE.search(elec.get("source", ""))
    if m:
        return datetime.fromisoformat(m.group(1) + "T00:00:00+00:00")
    return _iso(data["since"])


def _enrich(data: dict) -> dict:
    """Add ``monthly`` block with rates per month for every numeric counter.

    Most counters span the full `since→as_of` window. Electricity (and
    therefore cost_eur) only spans the Meross-daemon window, which is
    shorter. Mixing the two windows here would mis-scale kWh/day.
    """
    as_of = _iso(data["as_of"])
    since = _iso(data["since"])
    days_full = (as_of - since).total_seconds() / 86400
    days_elec = (as_of - _electricity_window_start(data)).total_seconds() / 86400
    if days_full <= 0 or days_elec <= 0:
        return data
    scale_full = DAYS_PER_MONTH / days_full
    scale_elec = DAYS_PER_MONTH / days_elec
    data["monthly"] = {
        "days_elapsed":             round(days_full, 1),
        "days_elapsed_electricity": round(days_elec, 1),
        "mist_cycles":   round(data["mist_cycles"]["count"] * scale_full),
        "electricity":   round(data["electricity"]["kwh"] * scale_elec, 1),
        "cost_eur":      round(data["cost_eur"]["value"] * scale_elec, 1),
        "co2_scrubbed":  round(data["co2_scrubbed"]["kg"] * scale_full, 2),
        "data_points":   round(data["data_points"]["count"] * scale_full),
        "fog_hours":     round(data["fog_hours"]["hours"] * scale_full, 1),
    }
    return data


def main() -> int:
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(URL, timeout=TIMEOUT_S, context=ctx) as r:
            data = json.loads(r.read())
    except Exception as e:
        if OUT.exists():
            print(f"fetch_ledger: {e}; keeping existing {OUT.name}", file=sys.stderr)
            return 0
        print(f"fetch_ledger: {e}; no fallback file present", file=sys.stderr)
        return 1

    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        print(f"fetch_ledger: response missing keys {missing}; refusing to overwrite",
              file=sys.stderr)
        return 1

    data = _enrich(data)
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    print(f"wrote -> {OUT.relative_to(OUT.parents[2])}")
    print(f"  since: {data['since']}")
    print(f"  as_of: {data['as_of']}")
    print(f"  window: {data['monthly']['days_elapsed']} days")
    print(f"  mist:  {data['mist_cycles']['count']:>10} total · {data['monthly']['mist_cycles']:>6}/month")
    print(f"  kwh:   {data['electricity']['kwh']:>10.2f} total · {data['monthly']['electricity']:>6.1f}/month")
    print(f"  cost:  €{data['cost_eur']['value']:>9.2f} total · €{data['monthly']['cost_eur']:>5.1f}/month")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
