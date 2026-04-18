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
from pathlib import Path

URL = "https://rei1.tail7cc014.ts.net/api/ledger.json"
OUT = Path(__file__).resolve().parents[1] / "data/ledger.json"
TIMEOUT_S = 10
REQUIRED_KEYS = ("since", "as_of", "mist_cycles", "electricity",
                 "cost_eur", "co2_scrubbed", "data_points", "fog_hours")


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

    OUT.write_text(json.dumps(data, indent=2) + "\n")
    print(f"wrote -> {OUT.relative_to(OUT.parents[2])}")
    print(f"  since: {data['since']}")
    print(f"  as_of: {data['as_of']}")
    print(f"  mist:  {data['mist_cycles']['count']:>10} cycles")
    print(f"  kwh:   {data['electricity']['kwh']:>10.2f}")
    print(f"  data:  {data['data_points']['count']:>10}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
