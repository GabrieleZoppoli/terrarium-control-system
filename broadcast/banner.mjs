// banner.mjs — Highland Cloud Forest broadcast event-banner controller.
//
// Writes /tmp/hcf_banner.txt once per second; broadcast.sh's ffmpeg drawtext
// reloads it every frame. Two sources, by priority:
//   1. MANUAL (highest) — a phone control page on :8091: countdown timers
//      ("MAINTENANCE IN m:ss"), a "door open now" banner, custom text.
//   2. AUTO (lower) — polls InfluxDB (read-only) for misting + photoperiod
//      transitions. Never touches the Node-RED control flows.
import http from "http";
import { writeFileSync } from "fs";

const PORT = 8091;
const BANNER_FILE = process.env.BANNER_FILE || "/tmp/hcf_banner.txt";
const INFLUX = "http://127.0.0.1:8086/query";
const DB = "highland";

let manual = null;     // { text, until:ms|null }
let countdown = null;  // { label, endsAt:ms, thenText, thenUntil:ms }
let auto = "";         // auto-event text
let autoExpire = 0;

function effective() {
  const now = Date.now();
  if (countdown) {
    const rem = Math.round((countdown.endsAt - now) / 1000);
    if (rem > 0) {
      const m = Math.floor(rem / 60), s = rem % 60;
      return `${countdown.label} ${m}:${String(s).padStart(2, "0")}`;
    }
    if (countdown.thenUntil && now < countdown.thenUntil) return countdown.thenText;
    countdown = null;
  }
  if (manual) {
    if (manual.until && now > manual.until) manual = null;
    else return manual.text;
  }
  if (now > autoExpire) auto = "";
  return auto || "";
}
setInterval(() => { try { writeFileSync(BANNER_FILE, effective()); } catch (e) {} }, 1000);

// ---- AUTO events from InfluxDB (read-only) ----
let prevLight = null;
function lastVal(result) {
  try {
    const row = result.series[0].values[0];   // [time, ...fields]
    return row[row.length - 1];
  } catch { return null; }
}
async function poll() {
  try {
    const q = encodeURIComponent(
      "SELECT last(*) FROM mister_status; SELECT last(*) FROM light_status");
    const r = await fetch(`${INFLUX}?db=${DB}&q=${q}`);
    const j = await r.json();
    const mister = lastVal(j.results[0]);
    const light = lastVal(j.results[1]);
    const now = Date.now();
    if (mister === 1) { auto = "• MISTING CYCLE"; autoExpire = now + 8000; }
    if (prevLight !== null && light !== prevLight) {
      auto = light === 1 ? "SUNRISE" : "NIGHTFALL";
      autoExpire = now + 60000;
    }
    prevLight = light;
  } catch (e) { /* influx down -> just no auto banner */ }
}
setInterval(poll, 4000); poll();

// ---- phone control page ----
const PAGE = `<!doctype html><html><head><meta name=viewport content="width=device-width,initial-scale=1">
<title>HCF banner</title><style>
body{font-family:system-ui,sans-serif;background:#0e1413;color:#e8efe9;margin:0;padding:18px}
h2{font-weight:600;font-size:20px}button{font-size:18px;padding:15px;margin:5px 0;width:100%;border:0;border-radius:12px;background:#1f9d6b;color:#fff}
button.warn{background:#c8553d}button.gray{background:#3a4441}input{font-size:18px;padding:13px;width:100%;box-sizing:border-box;border-radius:12px;border:0;margin:6px 0}
.row{display:flex;gap:8px}.row button{flex:1}.now{margin-top:14px;opacity:.7;font-size:15px}</style></head><body>
<h2>Highland Cloud Forest &mdash; banner</h2>
<p style=opacity:.6>Pre-announce a door opening to build suspense:</p>
<div class=row><button onclick="cd(60)">1&nbsp;min</button><button onclick="cd(180)">3&nbsp;min</button><button onclick="cd(300)">5&nbsp;min</button></div>
<button class=warn onclick="setT('DOOR OPEN — MAINTENANCE IN PROGRESS',0)">Door open now</button>
<input id=t placeholder="custom banner text">
<div class=row><button onclick="custom()">Show 60s</button><button class=gray onclick="clr()">Clear</button></div>
<p class=now id=s></p>
<script>
async function api(p){const r=await fetch(p,{method:'POST'});document.getElementById('s').textContent='→ '+await r.text();}
function cd(s){api('/countdown?secs='+s);}
function setT(t,ttl){api('/set?ttl='+ttl+'&text='+encodeURIComponent(t));}
function custom(){setT(document.getElementById('t').value||'',60);}
function clr(){api('/clear');}
</script></body></html>`;

http.createServer((req, res) => {
  const u = new URL(req.url, "http://x");
  if (req.method === "GET" && u.pathname === "/") {
    res.writeHead(200, { "Content-Type": "text/html" }); return res.end(PAGE);
  }
  const p = u.searchParams;
  const now = Date.now();
  if (u.pathname === "/set") {
    const ttl = +p.get("ttl") || 0;
    manual = { text: p.get("text") || "", until: ttl ? now + ttl * 1000 : null };
    countdown = null;
  } else if (u.pathname === "/countdown") {
    const secs = +p.get("secs") || 60;
    countdown = {
      label: "MAINTENANCE IN", endsAt: now + secs * 1000,
      thenText: "DOOR OPEN — MAINTENANCE IN PROGRESS",
      thenUntil: now + secs * 1000 + 600 * 1000,
    };
    manual = null;
  } else if (u.pathname === "/clear") {
    manual = null; countdown = null; auto = ""; autoExpire = 0;
  } else { res.writeHead(404); return res.end("?"); }
  res.writeHead(200, { "Content-Type": "text/plain" }); res.end(effective() || "(clear)");
}).listen(PORT, "0.0.0.0", () => console.log("banner control on :" + PORT));
