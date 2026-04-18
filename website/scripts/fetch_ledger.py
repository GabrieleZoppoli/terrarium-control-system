"""Fetch the Pi ledger endpoint and write ``website/data/ledger.json``.

Run before ``hugo`` to keep the homepage ledger values current. Falls back
to the previous file on fetch failure (Pi outages don't break deploys).
Idempotent; committing the resulting file is normal.
"""
from __future__ import annotations

import json
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


def _iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _enrich(data: dict) -> dict:
    """Add ``monthly`` block with rates per month for every numeric counter."""
    days = (_iso(data["as_of"]) - _iso(data["since"])).total_seconds() / 86400
    if days <= 0:
        return data
    scale = DAYS_PER_MONTH / days
    data["monthly"] = {
        "days_elapsed": round(days, 1),
        "mist_cycles":   round(data["mist_cycles"]["count"] * scale),
        "electricity":   round(data["electricity"]["kwh"] * scale, 1),
        "cost_eur":      round(data["cost_eur"]["value"] * scale, 1),
        "co2_scrubbed":  round(data["co2_scrubbed"]["kg"] * scale, 2),
        "data_points":   round(data["data_points"]["count"] * scale),
        "fog_hours":     round(data["fog_hours"]["hours"] * scale, 1),
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
