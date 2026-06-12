#!/usr/bin/env bash
# Stream a compressed image of the SD card to Google Drive via rclone,
# then prune all but the most recent KEEP backups.
#
# Manual test:   sudo /usr/local/bin/sd-backup-to-gdrive.sh
# Cron entry:    0 4 1 * *  /usr/local/bin/sd-backup-to-gdrive.sh
#                (runs at 04:00 on the 1st of every month)
#
# 2026-05-19 rewrite — was: `dd | pigz > /var/tmp/$NAME` then `rclone copyto`.
# Failure mode: /var/tmp is on the SD card being imaged, so the staged .img.gz
# eventually filled the very card it was reading from. Pigz hit ENOSPC, dd
# died of SIGPIPE, NR / InfluxDB / arduino-watchdog cascaded for hours. See
# memory/incident-2026-05-19-fan-cascade.md and memory/sd-backup-rclone.md.
# New design: stream dd → pigz → rclone rcat directly. No local temp file
# anywhere, so the cascade cannot recur. Trade-offs documented inline below.
#
# TODO future: for the root ext4 partition (/dev/mmcblk0p2), `e2image -ra -p`
# would skip empty blocks at the FS level and cut runtime dramatically. Would
# need a two-step layout (dd the small FAT boot partition, e2image the root)
# and a non-dd restore path. Deferred — current streaming version is safe
# even if slow.

set -o pipefail
exec 9>/var/run/sd-backup.lock
flock -n 9 || { echo "$(date -Is) another backup is already running"; exit 1; }

DEV=/dev/mmcblk0
REMOTE=gdrive:terrarium-backups
KEEP=3
DATE=$(date +%F)
NAME="rei1-${DATE}.img.gz"
LOG=/var/log/sd-backup.log

# rclone runs as pi (where the oauth token lives), not root
RCLONE_USER=pi
RCLONE_HOME=/home/pi

# Minimum acceptable uploaded size — anything below this means dd or pigz
# emitted almost nothing, which means the upload "succeeded" with garbage.
# A 128 GB SD with 26 GB used compresses to ~8–12 GB; even very-sparse data
# should be well above 100 MB. Anything under 100 MB is wrong.
MIN_SIZE_BYTES=$((100 * 1024 * 1024))

log() { echo "$(date -Is) $*" >> "$LOG"; }

log "=== start $NAME (streaming dd | pigz | rclone rcat — no local stage) ==="
START=$(date +%s)

sync

# Single-pass pipeline: dd reads from SD, pigz compresses, rclone uploads
# stdin to a remote object atomically. No local file is ever created. The
# only state on disk during the run is the lock file (a few bytes).
#
# rclone rcat trade-off: no resume capability. If the network drops mid-
# upload, the whole stream is lost. Acceptable for a monthly cron job; if
# this becomes problematic, switch to `rclone copyto --tpslimit 1` against
# a tmpfs-staged file (but tmpfs is < image size, so this needs e2image
# or partclone to shrink the input first).
#
# Note: dd progress goes to stderr (the 2>>"$LOG") so the LOG will have
# the per-second byte-count lines as before. pigz and rclone both write
# their own progress to stderr too — same destination.
sudo -u "$RCLONE_USER" HOME="$RCLONE_HOME" rclone --version >>"$LOG" 2>&1

dd if="$DEV" bs=4M status=progress iflag=fullblock 2>>"$LOG" \
  | pigz -1 -p 3 2>>"$LOG" \
  | sudo -u "$RCLONE_USER" HOME="$RCLONE_HOME" \
      rclone rcat --stats=1m --stats-one-line "$REMOTE/$NAME" 2>>"$LOG"

# PIPESTATUS captures all three stage exit codes. With set -o pipefail, the
# overall $? is the rightmost non-zero, but we want to log specifically
# which stage failed.
DD_RC=${PIPESTATUS[0]}
PIGZ_RC=${PIPESTATUS[1]}
RCLONE_RC=${PIPESTATUS[2]}
ELAPSED=$(( $(date +%s) - START ))

if [ "$DD_RC" -ne 0 ] || [ "$PIGZ_RC" -ne 0 ] || [ "$RCLONE_RC" -ne 0 ]; then
  log "FAIL $NAME dd_rc=$DD_RC pigz_rc=$PIGZ_RC rclone_rc=$RCLONE_RC elapsed=${ELAPSED}s"
  # If rclone got partway through, gdrive may have a partial object — try to
  # remove it so the next month's backup isn't blocked by a half-upload.
  sudo -u "$RCLONE_USER" HOME="$RCLONE_HOME" \
    rclone deletefile "$REMOTE/$NAME" 2>/dev/null && log "cleaned up partial $NAME on remote"
  exit 1
fi

# Verify the uploaded size is plausible (catches the "successful upload of
# 12 bytes" failure mode).
SIZE=$(sudo -u "$RCLONE_USER" HOME="$RCLONE_HOME" \
  rclone lsl "$REMOTE/$NAME" 2>/dev/null | awk '{print $1}')

if [ -z "$SIZE" ]; then
  log "FAIL $NAME upload reported success but remote file not found"
  exit 2
fi

if [ "$SIZE" -lt "$MIN_SIZE_BYTES" ]; then
  log "FAIL $NAME uploaded size=$SIZE bytes is below MIN_SIZE_BYTES=$MIN_SIZE_BYTES — likely corrupt"
  sudo -u "$RCLONE_USER" HOME="$RCLONE_HOME" \
    rclone deletefile "$REMOTE/$NAME" 2>/dev/null && log "removed suspect $NAME"
  exit 3
fi

log "ok $NAME bytes=$SIZE elapsed=${ELAPSED}s rate=$((SIZE / ELAPSED / 1024))KB/s"

# Prune: list newest-first, skip the first $KEEP, delete the rest.
sudo -u "$RCLONE_USER" HOME="$RCLONE_HOME" \
  rclone lsf --files-only --format "tp" "$REMOTE" 2>>"$LOG" \
  | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9:]+;rei1-.*\.img\.gz$' \
  | sort -r \
  | tail -n +$((KEEP + 1)) \
  | cut -d';' -f2 \
  | while read -r OLD; do
      log "prune $OLD"
      sudo -u "$RCLONE_USER" HOME="$RCLONE_HOME" rclone deletefile "$REMOTE/$OLD" 2>>"$LOG"
    done

log "=== end $NAME ==="
