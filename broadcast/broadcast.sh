#!/bin/bash
# broadcast.sh — Highland Cloud Forest 24/7 composite encoder.
#
# Composites the cabinet camera (left ~65%) with the live Node-RED dashboard
# (right ~35%), adds title + clock chrome, hardware-encodes H.264, and writes
# to OUT. OUT decides the sink:
#   - a local file  (e.g. /tmp/test.mp4)  -> for preview / validation
#   - an rtmp(s):// URL                   -> YouTube Live ingest
#
# Inputs are two MJPEG-over-HTTP streams served on localhost:
#   :8080  ustreamer  (terrarium-cam.service)   -> the UVC camera
#   :8090  puppeteer  (terrarium-dash.service)  -> the Node-RED /ui dashboard
#
# Usage:  broadcast.sh [OUT] [DURATION_SECONDS]
#   OUT       default /tmp/p2_test.mp4
#   DURATION  optional; if set, ffmpeg stops after N seconds (testing)
set -euo pipefail

CAM_URL="${CAM_URL:-http://localhost:8080/stream}"
DASH_URL="${DASH_URL:-http://127.0.0.1:8090/}"
FONT="${FONT:-/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf}"

OUT="${1:-/tmp/p2_test.mp4}"
DURATION="${2:-}"

# Live event banner: ffmpeg re-reads this file every frame (drawtext reload=1).
# Empty file => no banner. The banner controller (banner.mjs) writes it.
BANNER_FILE="${BANNER_FILE:-/tmp/hcf_banner.txt}"
touch "$BANNER_FILE"

# Canvas 1920x1080. Camera region 1248px (65%), dashboard 672px (35%).
VBITRATE="${VBITRATE:-4500k}"
FPS="${FPS:-25}"
GOP="${GOP:-50}"          # 2s keyframe interval at 25fps (YouTube-friendly)

# Pick the muxer from the sink.
case "$OUT" in
  rtmp://*|rtmps://*) FMT="flv" ;;
  *.mp4)              FMT="mp4" ;;
  *.mkv)              FMT="matroska" ;;
  *)                  FMT="${OUT##*.}" ;;
esac

DUR_ARGS=()
[ -n "$DURATION" ] && DUR_ARGS=(-t "$DURATION")

# Filtergraph:
#   - crop the 1920x1080 camera to the left region (center horizontal crop)
#   - scale the dashboard to the right region
#   - hstack them
#   - draw the title + a live clock over the camera's top-left
FILTER="\
[0:v]crop=1248:1080:336:0,setsar=1[cam];\
[1:v]scale=672:1080,setsar=1[dash];\
[cam][dash]hstack=inputs=2[base];\
[base]drawtext=fontfile=${FONT}:text='HIGHLAND CLOUD FOREST':x=30:y=26:fontsize=38:fontcolor=white:box=1:boxcolor=black@0.45:boxborderw=14,\
drawtext=fontfile=${FONT}:text='%{localtime}':x=30:y=82:fontsize=24:fontcolor=white@0.88:box=1:boxcolor=black@0.32:boxborderw=9,\
drawtext=fontfile=${FONT}:textfile=${BANNER_FILE}:reload=1:x=(1248-tw)/2:y=h-150:fontsize=46:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=22[v]"

exec ffmpeg -hide_banner -loglevel "${LOGLEVEL:-warning}" \
  -f mpjpeg -thread_queue_size 64 -i "$CAM_URL" \
  -f mpjpeg -thread_queue_size 16 -i "$DASH_URL" \
  -filter_complex "$FILTER" \
  -map "[v]" \
  -c:v h264_v4l2m2m -b:v "$VBITRATE" -pix_fmt yuv420p -g "$GOP" -r "$FPS" \
  "${DUR_ARGS[@]}" \
  -f "$FMT" -y "$OUT"
