# Reporting and alerts

Two scripts, two jobs:

| Script | When | What you get |
|---|---|---|
| `terrarium-health.py` | every 5 min | An email **only when something is wrong**, naming the problem in the subject (`🔴 Terrarium: Arduino serial stale (190s)`), with when it started. A "cleared" email when a warning goes away. |
| `terrarium-report.py` | 07:00 daily, 21:00 if needed | One structured report: what needs attention, a plain-language summary, every key number against what is usual, freezer behaviour, water-tank forecast, alert episodes, system health. |

The 6-hourly "🟢 Terrarium OK" emails and the old sitrep digests are switched
off; the 07:00 report is the daily heartbeat. If it doesn't arrive, something
is wrong with the Pi.

## What "smart" means here

* **Compared with itself.** Each number is checked against the same hours on
  each of the previous 7 days (median, and a robust z-score from the spread).
  21 °C at 14:00 and 21 °C at 03:00 are judged differently.
* **Only meaningful changes are flagged.** Both the z-score (≥ 3) and a minimum
  size of change (e.g. 0.5 °C, 3 pp humidity, 8 pp freezer duty) must be met.
* **Causes, where it can tell.** A busier freezer with a warmer room is noted as
  explained; a busier freezer without one is flagged (door seal, frost, fans).
* **Forecasts.** Water tank use per day since the last refill → when to refill.
  Disk growth → days until 85 %.
* **Episodes, not counts.** Health-check alerts are grouped into episodes with
  start, end and duration.
* **What changed.** Each report saves a JSON snapshot; the next one lists new
  and cleared problems.
* **Quiet evenings.** The 21:00 run sends only if something is yellow/red or
  changed since the morning.

## Install on the Pi

One command, run on the Pi as user `pi` (ssh in, or a terminal on the Pi):

```bash
curl -fsSL https://raw.githubusercontent.com/GabrieleZoppoli/terrarium-control-system/claude/raspberry-pi-terrarium-debug-zsiv9y/scripts/install-reporting.sh | bash
```

`scripts/install-reporting.sh` checks the running health script matches the
repo (it stops rather than overwrite Pi-only edits), moves the existing
passwords into `/etc/terrarium/secrets.env`, installs both scripts with
backups, test-runs the report, and swaps the sitrep crontab lines for the
report ones. Add `-s -- --send-test` after `bash` to also email a report
straight away. It prints the commands to undo everything at the end.

### Manual install

```bash
# 1. Secrets (shared by both scripts)
sudo mkdir -p /etc/terrarium
sudo cp scripts/terrarium-secrets.env.example /etc/terrarium/secrets.env
sudo nano /etc/terrarium/secrets.env          # fill in Gmail/Tapo values from the old scripts
sudo chown pi:pi /etc/terrarium/secrets.env && sudo chmod 600 /etc/terrarium/secrets.env

# 2. Scripts (repo copies have no credentials; they read secrets.env)
sudo cp /usr/local/bin/terrarium-health.py /usr/local/bin/terrarium-health.py.bak_$(date +%Y%m%d)
sudo install -m 755 scripts/terrarium-health.py  /usr/local/bin/terrarium-health.py
sudo install -m 755 scripts/terrarium-report.py  /usr/local/bin/terrarium-report.py

# 3. Try it (prints to the terminal, sends nothing)
python3 /usr/local/bin/terrarium-report.py
python3 /usr/local/bin/terrarium-report.py --format html > /tmp/report.html

# 4. Schedule: edit pi's crontab
crontab -e
```

In the crontab, remove (or comment out) the two `terrarium-sitrep.py --email`
lines and add:

```cron
0 7  * * * /usr/bin/python3 /usr/local/bin/terrarium-report.py --email 2>&1 | logger -t terrarium-report
0 21 * * * /usr/bin/python3 /usr/local/bin/terrarium-report.py --email --hours 12 --quiet-if-green 2>&1 | logger -t terrarium-report
```

Leave the existing `*/5` `terrarium-health.py` line as it is.

The first few days the report has little history: alert episodes and the
water forecast start once the new health check has written its ledger
(`~/.terrarium-health-ledger.jsonl`), and "usual" values need InfluxDB data
from the previous days (already there). Disk-growth forecasts need about four
saved reports.

## Files it writes

| Path | What | Size |
|---|---|---|
| `~/.terrarium-health-ledger.jsonl` | One line per health check (status, warnings, water %, temp, humidity, power) | ~75 KB/day, trimmed to 21 days |
| `~/terrarium-reports/report-YYYYMMDD-HHMM.json` | Full structured report | ~15 KB each, kept 90 days |

The JSON snapshots are easy to load later (R: `jsonlite::fromJSON()`;
Python: `json.load`) for longer-term analysis.

## Tuning

Every threshold is a `TERRARIUM_*` line in `/etc/terrarium/secrets.env`;
see `scripts/terrarium-secrets.env.example` for the list and defaults.

## Other changes in terrarium-health.py

* Credentials read from `/etc/terrarium/secrets.env` (the in-file constants
  are only fallbacks), so the repo copy deploys unchanged.
* Time-of-day checks (freezer daytime window etc.) use Europe/Rome time.
  Before, they used a fixed UTC+2, an hour off from late October to late March.
* Alert emails are HTML with the problem list first; WhatsApp is unchanged.
