#!/bin/bash
# make_ambient.sh — generate a relaxing highland-cloud-forest ambient bed.
# Fully synthesized (sox) => CC0, no YouTube Content-ID risk. No gongs, no birds.
# Layers: brown-noise wind/mist + a quiet airy mist + scattered water drops.
#
# Usage: make_ambient.sh [DURATION_SEC] [OUT.wav]
set -euo pipefail
DUR="${1:-40}"
OUT="${2:-/tmp/ambient_sample.wav}"
R=44100
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# --- wind/mist bed: brown noise, low-passed, slow swell, roomy reverb ---
sox -n -r $R -c 2 "$TMP/bed.wav" synth "$DUR" brownnoise \
  lowpass 470 highpass 70 \
  tremolo 0.07 45 \
  reverb 55 50 80 \
  vol 0.42

# --- thin airy mist layer: quiet band-passed pink noise ---
sox -n -r $R -c 2 "$TMP/mist.wav" synth "$DUR" pinknoise \
  bandpass 1700 900 \
  tremolo 0.05 55 \
  reverb 70 60 90 \
  vol 0.05

# --- water-drop one-shots: short resonant noise burst + reverb tail (varied pitch) ---
mk_drop(){  # $1 out  $2 centerHz
  sox -n -r $R -c 2 "$1" synth 0.035 pinknoise \
    band -n "$2" 300 \
    pad 0 0.6 \
    reverb 78 55 90 \
    fade h 0 0.62 0.5 \
    gain -3
}
mk_drop "$TMP/d1.wav" 950
mk_drop "$TMP/d2.wav" 1300
mk_drop "$TMP/d3.wav" 1750
mk_drop "$TMP/d4.wav" 2200
mk_drop "$TMP/d5.wav" 820

# --- assemble a drops track: random gap, random drop, until ~DUR ---
seq=""
total=0
i=0
while awk -v t="$total" -v d="$DUR" 'BEGIN{exit !(t < d-1)}'; do
  gap=$(awk -v r="$RANDOM" 'BEGIN{printf "%.3f", 1.3 + (r/32767.0)*4.6}')   # 1.3–5.9s
  sox -n -r $R -c 2 "$TMP/g$i.wav" trim 0 "$gap"
  dn=$(( RANDOM % 5 + 1 ))
  seq="$seq $TMP/g$i.wav $TMP/d$dn.wav"
  total=$(awk -v t="$total" -v g="$gap" 'BEGIN{printf "%.3f", t+g+0.6}')
  i=$((i+1))
done
# shellcheck disable=SC2086
sox $seq "$TMP/drops.wav"

# --- final mix: bed + mist + drops, gentle normalize, fade in/out ---
sox -m "$TMP/bed.wav" "$TMP/mist.wav" "$TMP/drops.wav" "$OUT" \
  gain -n -2 \
  fade t 2.5 "$DUR" 3.5

echo "wrote $OUT ($(soxi -D "$OUT" 2>/dev/null)s)"
