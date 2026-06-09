#!/bin/bash
# broadcast.sh — Highland Cloud Forest 24/7 composite encoder.
#
# Composites the cabinet camera (left ~65%) with the live Node-RED dashboard
# (right ~35%), title + clock + live event banner, mixes the cabinet mic with a
# generated ambient bed, hardware-encodes H.264/AAC, and writes to OUT.
#   OUT = local file (e.g. /tmp/test.mp4)  -> preview / validation
#   OUT = rtmp(s):// URL                   -> YouTube Live ingest
#
# Inputs (all localhost):
#   :8080 ustreamer  (terrarium-cam)    -> UVC camera (MJPEG)
#   :8090 puppeteer  (terrarium-dash)   -> Node-RED /ui dashboard (MJPEG)
#   ALSA  plughw:CARD=Camera            -> camera microphone
#   file  $AMBIENT                      -> looped ambient bed (make_ambient.sh)
#   file  $BANNER_FILE                  -> live event-banner text (banner.mjs)
#
# Usage:  broadcast.sh [OUT] [DURATION_SECONDS]
set -euo pipefail

CAM_URL="${CAM_URL:-http://localhost:8080/stream}"
DASH_URL="${DASH_URL:-http://127.0.0.1:8090/}"
FONT="${FONT:-/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf}"
BANNER_FILE="${BANNER_FILE:-/tmp/hcf_banner.txt}"
AMBIENT="${AMBIENT:-/home/pi/terrarium-broadcast/ambient_bed.wav}"
MIC="${MIC:-plughw:CARD=Camera}"
AUDIO="${AUDIO:-1}"                       # set 0 for video-only

OUT="${1:-/tmp/p2_test.mp4}"
DURATION="${2:-}"
touch "$BANNER_FILE"

VBITRATE="${VBITRATE:-4500k}"
ABITRATE="${ABITRATE:-128k}"
FPS="${FPS:-25}"
GOP="${GOP:-50}"                          # 2s keyframe interval @25fps

case "$OUT" in
  rtmp://*|rtmps://*) FMT="flv" ;;
  *.mp4)              FMT="mp4" ;;
  *.mkv)              FMT="matroska" ;;
  *)                  FMT="${OUT##*.}" ;;
esac

# --- video filtergraph: crop camera to left 65%, dashboard to right 35%,
#     hstack, then title + live clock + reloaded event banner ---
FILTER="\
[0:v]crop=1248:1080:336:0,format=yuv420p,setsar=1[cam];\
[1:v]scale=672:1080,format=yuv420p,setsar=1[dash];\
[cam][dash]hstack=inputs=2[base];\
[base]drawtext=fontfile=${FONT}:text='HIGHLAND CLOUD FOREST':x=30:y=26:fontsize=38:fontcolor=white:box=1:boxcolor=black@0.45:boxborderw=14,\
drawtext=fontfile=${FONT}:text='%{localtime}':x=30:y=82:fontsize=24:fontcolor=white@0.88:box=1:boxcolor=black@0.32:boxborderw=9,\
drawtext=fontfile=${FONT}:textfile=${BANNER_FILE}:reload=1:x=(1248-tw)/2:y=h-150:fontsize=46:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=22[v]"

# --- inputs / maps (audio optional) ---
INPUTS=(-f mpjpeg -thread_queue_size 512 -i "$CAM_URL"
        -f mpjpeg -thread_queue_size 64  -i "$DASH_URL")
MAPS=(-map "[v]")
ACODEC=()
if [ "$AUDIO" = "1" ]; then
  INPUTS+=(-thread_queue_size 4096 -f alsa -ac 1 -ar 44100 -i "$MIC"
           -stream_loop -1 -i "$AMBIENT")
  # mic: resync (async resample absorbs ALSA jitter/xruns) + de-rumble + gentle
  # compression/limit;  ambient: quieter bed;  mix
  FILTER="$FILTER;\
[2:a]aresample=async=1000:min_hard_comp=0.100:first_pts=0,highpass=f=110,acompressor=threshold=-20dB:ratio=3:attack=15:release=250,alimiter=limit=0.9,volume=0.85[mic];\
[3:a]volume=0.55[amb];\
[mic][amb]amix=inputs=2:duration=first:normalize=0[a]"
  MAPS+=(-map "[a]")
  ACODEC=(-c:a aac -b:a "$ABITRATE" -ar 44100)
fi

DUR_ARGS=()
[ -n "$DURATION" ] && DUR_ARGS=(-t "$DURATION")

exec ffmpeg -hide_banner -loglevel "${LOGLEVEL:-warning}" \
  "${INPUTS[@]}" \
  -filter_complex "$FILTER" \
  "${MAPS[@]}" \
  -c:v h264_v4l2m2m -b:v "$VBITRATE" -pix_fmt yuv420p -g "$GOP" -r "$FPS" \
  "${ACODEC[@]}" \
  "${DUR_ARGS[@]}" \
  -f "$FMT" -y "$OUT"
