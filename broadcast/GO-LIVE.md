# Highland Cloud Forest — go-live runbook

Everything is built and validated. Going live is three steps once the YouTube
24-hour activation completes.

## Services (all on `rei1`, the control Pi)

| Service | Role | Port | Runs |
|---|---|---|---|
| `terrarium-cam` | ustreamer — camera MJPEG, 1080p30 | :8080 | always |
| `terrarium-dash` | puppeteer — Node-RED `/ui` as MJPEG | :8090 | with the stream |
| `terrarium-banner` | event-banner controller + phone UI | :8091 | always |
| `terrarium-thermal-guard` | pauses stream if SoC ≥78 °C | — | always |
| `terrarium-stream` | the ffmpeg composite → YouTube | — | **go-live** |

Camera view (LAN or Tailscale): `http://<pi>:8080/` · Banner control: `http://<pi>:8091/`
(`<pi>` = `192.168.1.168` on the home LAN, `100.75.138.32` over Tailscale.)

## Go-live — 3 steps

1. **Aim the camera** at the cabinet using the `:8080` view; twist the lens
   barrel (anticlockwise = closer) until the plants are sharp.

2. **Add the stream key.** In YouTube Studio → Go Live → **Stream**, copy the
   **Stream key**. On the Pi:
   ```bash
   cd /home/pi/terrarium-broadcast
   cp stream.env.example stream.env
   chmod 600 stream.env
   nano stream.env      # set STREAM_URL=rtmp://a.rtmp.youtube.com/live2/<YOUR-KEY>
   ```

3. **Start the broadcast:**
   ```bash
   sudo systemctl enable --now terrarium-stream.service
   journalctl -u terrarium-stream -f      # watch it connect
   ```
   The YouTube Live dashboard will show the incoming stream within ~30 s; click
   **Go Live** there (or use a scheduled stream).

## Operating it

- **Suspense banner**: open `http://<pi>:8091/` on your phone → tap a maintenance
  countdown before opening the cabinet, or "Door open now", or custom text.
- **Auto-captions** (misting, sunrise/nightfall) fire on their own from InfluxDB.
- **Stop**: `sudo systemctl stop terrarium-stream` (the grabber stops with it).
- **Thermal safety**: the guard pauses the stream at 78 °C and resumes at 68 °C.
  Measured load runs ~56–58 °C, so this is just a backstop.

## Tunables

- Resolution/bitrate/fps: env vars at the top of `broadcast.sh`.
- Ambient sound: re-run `make_ambient.sh <seconds> ambient_bed.wav` to regenerate
  (longer = less obvious loop; adjust drop/bed params inside the script).
- Audio off (video only): `AUDIO=0` env on `broadcast.sh`.

## Open / optional

- **Door auto-detection** isn't wired (no InfluxDB door measurement found); the
  manual "Door open" button covers it. Auto would need a door signal source.
- **"Day N" counter** and a YouTube-embed on highlandcloudforest.com are optional
  later polish.
