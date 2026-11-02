#!/usr/bin/env bash
# One-shot installer for the new reporting (docs/reporting.md).
# Run on the Pi as user pi:
#
#   curl -fsSL https://raw.githubusercontent.com/GabrieleZoppoli/terrarium-control-system/claude/raspberry-pi-terrarium-debug-zsiv9y/scripts/install-reporting.sh | bash
#
# What it does (each step is undoable; backups are printed at the end):
#   1. Downloads terrarium-report.py and the new terrarium-health.py.
#   2. Checks the health script running on the Pi matches the repo copy
#      (credentials aside). If it has Pi-only edits, it stops instead of
#      overwriting them.
#   3. Moves the passwords from the running health script into
#      /etc/terrarium/secrets.env (chmod 600). Values are never printed.
#   4. Installs both scripts into /usr/local/bin (old one backed up).
#   5. Test-runs the report (prints it, sends nothing).
#   6. Crontab: comments out the sitrep email lines, adds the 07:00 / 21:00
#      report lines (crontab backed up).
#
# Flags:  --send-test   also email a report right away
#         --force       replace the health script even if it has Pi-only edits
set -euo pipefail

BRANCH="${BRANCH:-claude/raspberry-pi-terrarium-debug-zsiv9y}"
BASE_COMMIT="3ca9181e7235acefca4ced1535aaf27a4e4f676e"   # health check as deployed on the Pi
RAW="https://raw.githubusercontent.com/GabrieleZoppoli/terrarium-control-system"
BIN_DIR="${BIN_DIR:-/usr/local/bin}"
ETC_DIR="${ETC_DIR:-/etc/terrarium}"
SRC_DIR="${SRC_DIR:-}"          # use local files instead of downloading (testing)
SUDO="${SUDO-sudo}"
CRONTAB="${CRONTAB:-crontab}"

SEND_TEST=0; FORCE=0
for a in "$@"; do
  case "$a" in
    --send-test) SEND_TEST=1 ;;
    --force) FORCE=1 ;;
    *) echo "unknown option: $a" >&2; exit 2 ;;
  esac
done

say()  { printf '\n\033[1m▶ %s\033[0m\n' "$*"; }
ok()   { printf '  ✓ %s\n' "$*"; }
die()  { printf '  ✗ %s\n' "$*" >&2; exit 1; }

STAMP=$(date +%Y%m%d-%H%M%S)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

HEALTH="$BIN_DIR/terrarium-health.py"
REPORT="$BIN_DIR/terrarium-report.py"
SECRETS="$ETC_DIR/secrets.env"

# ── 0. Preconditions ───────────────────────────────────────────────────
say "Checking the Pi"
[ -f "$HEALTH" ] || die "$HEALTH not found. Is this the terrarium Pi?"
python3 -c 'import sys, zoneinfo; assert sys.version_info >= (3, 9)' 2>/dev/null \
  || die "need Python 3.9+ with zoneinfo"
curl -fsS -m 5 "http://localhost:8086/ping" >/dev/null 2>&1 \
  && ok "InfluxDB answering" || echo "  ! InfluxDB not answering on :8086 (continuing)"
ok "python $(python3 -V 2>&1 | cut -d' ' -f2), $HEALTH present"

# ── 1. Fetch ───────────────────────────────────────────────────────────
say "Fetching scripts ($BRANCH)"
fetch() {  # fetch <ref> <repo path> <dest>
  if [ -n "$SRC_DIR" ]; then
    case "$1" in
      "$BASE_COMMIT") git -C "$SRC_DIR" show "$1:$2" > "$3" ;;
      *) cp "$SRC_DIR/$2" "$3" ;;
    esac
  else
    curl -fsSL -m 30 "$RAW/$1/$2" -o "$3"
  fi
}
fetch "$BRANCH" scripts/terrarium-report.py "$WORK/terrarium-report.py"
fetch "$BRANCH" scripts/terrarium-health.py "$WORK/terrarium-health.py"
fetch "$BASE_COMMIT" scripts/terrarium-health.py "$WORK/health-base.py"
for f in terrarium-report.py terrarium-health.py; do
  python3 -m py_compile "$WORK/$f" || die "$f does not compile"
done
ok "downloaded and compiled"

# ── 2. Is the running health script the one in the repo? ──────────────
say "Comparing the running health check with the repo"
ALREADY_NEW=0
if grep -q "TERRARIUM_GMAIL_APP_PASS" "$HEALTH"; then
  ALREADY_NEW=1
  ok "already the new version (reads secrets.env)"
else
  CRED_RE='^(GMAIL_ADDRESS|GMAIL_APP_PASS|GMAIL_TO|PHONE|CALLMEBOT_KEY|TAPO_EMAIL|TAPO_PASS)[[:space:]]*='
  grep -Ev "$CRED_RE" "$HEALTH" > "$WORK/running.norm"
  grep -Ev "$CRED_RE" "$WORK/health-base.py" > "$WORK/base.norm"
  if diff -q "$WORK/base.norm" "$WORK/running.norm" >/dev/null; then
    ok "identical to the repo apart from credentials, safe to replace"
  else
    echo "  ! The Pi's copy differs from the repo (not just passwords):"
    diff -u "$WORK/base.norm" "$WORK/running.norm" | sed -n '3,40p' | sed 's/^/    /'
    if [ "$FORCE" = 1 ]; then
      echo "  ! --force given: replacing anyway (backup kept)"
    else
      die "stopping so Pi-only edits aren't lost. Share the diff above, or rerun with --force."
    fi
  fi
fi

# ── 3. Secrets ─────────────────────────────────────────────────────────
say "Secrets file"
if [ -f "$SECRETS" ]; then
  ok "$SECRETS exists, leaving it as is"
elif [ "$ALREADY_NEW" = 1 ]; then
  die "$HEALTH is already the new version but $SECRETS is missing; create it from scripts/terrarium-secrets.env.example"
else
  python3 - "$HEALTH" "$WORK/secrets.env" <<'PY'
import re, sys
src, out = sys.argv[1], sys.argv[2]
names = {"GMAIL_ADDRESS": "TERRARIUM_GMAIL_ADDRESS", "GMAIL_APP_PASS": "TERRARIUM_GMAIL_APP_PASS",
         "GMAIL_TO": "TERRARIUM_GMAIL_TO", "PHONE": "TERRARIUM_WHATSAPP_PHONE",
         "CALLMEBOT_KEY": "TERRARIUM_CALLMEBOT_KEY", "TAPO_EMAIL": "TERRARIUM_TAPO_EMAIL",
         "TAPO_PASS": "TERRARIUM_TAPO_PASS"}
text = open(src).read()
lines, found, missing = [], [], []
for k, new in names.items():
    m = re.search(rf'^{k}\s*=\s*(["\'])(.*?)\1', text, re.M)
    v = m.group(2) if m else ""
    if not v or v.startswith("REDACTED") or v == "XXXXXX":
        missing.append(k)
        if k == "CALLMEBOT_KEY":
            lines.append(f"{new}=")       # empty = WhatsApp off, as before
        continue
    lines.append(f"{new}={v}")
    found.append(k)
lines.append("# 0 = no periodic 'all green' email (the 07:00 report is the heartbeat)")
lines.append("TERRARIUM_GREEN_EMAIL_HOURS=0")
open(out, "w").write("# Created by install-reporting.sh. Tuning options: scripts/terrarium-secrets.env.example\n"
                     + "\n".join(lines) + "\n")
print("  ✓ copied: " + ", ".join(found))
if missing:
    print("  ! not set in the running script: " + ", ".join(missing))
if not {"GMAIL_ADDRESS", "GMAIL_APP_PASS", "GMAIL_TO"} <= set(found):
    sys.exit("  ✗ Gmail settings not found; refusing to continue (alerts would stop)")
PY
  $SUDO mkdir -p "$ETC_DIR"
  $SUDO install -m 600 -o "$(id -un)" -g "$(id -gn)" "$WORK/secrets.env" "$SECRETS"
  ok "wrote $SECRETS (mode 600, values not shown)"
fi

# ── 4. Install ─────────────────────────────────────────────────────────
say "Installing scripts"
HEALTH_BAK="$HEALTH.bak_$STAMP"
$SUDO cp -p "$HEALTH" "$HEALTH_BAK"
ok "backup: $HEALTH_BAK"
$SUDO install -m 755 "$WORK/terrarium-health.py" "$HEALTH"
$SUDO install -m 755 "$WORK/terrarium-report.py" "$REPORT"
ok "installed $HEALTH and $REPORT"

rollback() {
  echo "  ✗ $1, restoring the previous health check" >&2
  $SUDO cp -p "$HEALTH_BAK" "$HEALTH"
  exit 1
}

# ── 5. Test ────────────────────────────────────────────────────────────
say "Test run (nothing is sent)"
python3 -c "
import importlib.util as u
s = u.spec_from_file_location('h', '$HEALTH'); m = u.module_from_spec(s); s.loader.exec_module(m)
assert not m.GMAIL_APP_PASS.startswith('REDACTED'), 'secrets not picked up'
" || rollback "new health check can't read its settings"
ok "health check loads and reads secrets.env"
if ! python3 "$REPORT" --no-save > "$WORK/report.txt" 2> "$WORK/report.err"; then
  cat "$WORK/report.err" >&2
  rollback "report failed"
fi
sed -n '1,40p' "$WORK/report.txt" | sed 's/^/    /'

# ── 6. Crontab ─────────────────────────────────────────────────────────
say "Crontab"
CRON_BAK="$HOME/crontab.bak_$STAMP"
$CRONTAB -l > "$CRON_BAK" 2>/dev/null || true
ok "backup: $CRON_BAK"
python3 - "$CRON_BAK" "$WORK/crontab.new" "$REPORT" <<'PY'
import sys
src, out, report = sys.argv[1:4]
lines = open(src).read().splitlines()
new, disabled = [], 0
for l in lines:
    s = l.strip()
    if not s.startswith("#") and "terrarium-sitrep" in s and "--email" in s:
        new.append("# disabled by install-reporting.sh (replaced by terrarium-report.py): " + l)
        disabled += 1
    else:
        new.append(l)
if not any("terrarium-report.py" in l and not l.strip().startswith("#") for l in lines):
    new += ["",
            "# Terrarium report (docs/reporting.md)",
            f"0 7  * * * /usr/bin/python3 {report} --email 2>&1 | logger -t terrarium-report",
            f"0 21 * * * /usr/bin/python3 {report} --email --hours 12 --quiet-if-green 2>&1 | logger -t terrarium-report"]
    print("  ✓ added 07:00 and 21:00 report lines")
else:
    print("  ✓ report lines already present")
already = any("disabled by install-reporting.sh" in l for l in lines)
if disabled:
    print(f"  ✓ disabled {disabled} sitrep email line(s)")
elif already:
    print("  ✓ sitrep email lines already disabled")
else:
    print("  ! no sitrep email line in this crontab (check: sudo crontab -l, /etc/cron.d)")
open(out, "w").write("\n".join(new) + "\n")
PY
$CRONTAB "$WORK/crontab.new"
ok "crontab updated"
$CRONTAB -l | grep -E "terrarium-(health|report)" | grep -v '^#' | sed 's/^/    /' || true
if ! $CRONTAB -l 2>/dev/null | grep -q "terrarium-health.py"; then
  echo "  ! terrarium-health.py is not in this user's crontab; check 'sudo crontab -l' or /etc/cron.d"
fi

# ── 7. Optional email ──────────────────────────────────────────────────
if [ "$SEND_TEST" = 1 ]; then
  say "Sending a test report"
  python3 "$REPORT" --email --no-save && ok "sent, check your inbox"
fi

say "Done"
cat <<EOF
  Next report: 07:00. The health check picks up the new version at its next 5-min run.
  Undo everything:
    sudo cp -p $HEALTH_BAK $HEALTH
    crontab $CRON_BAK
    sudo rm $REPORT        # optional
EOF
