"""Vision inputs: best frame pick, overview/crops, prompt."""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date as _date, timedelta
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw

from . import annotate, config, registry, storage

CROP = 400
GRID = 100


def pick_best(day_dir) -> Optional[Path]:
    day_dir = Path(day_dir)
    try:
        frames = json.loads((day_dir / "day.json").read_text())["frames"]
        if not isinstance(frames, list):
            return None
    except (OSError, ValueError, KeyError, TypeError):
        return None
    cands = {"plateau": [], "lit": []}
    for fr in frames:
        try:
            phase = fr["phase"]
            if phase not in cands:
                continue
            files, sharp = fr["files"], fr["sharpness"]
            if not isinstance(files, list) or not isinstance(sharp, list) \
                    or len(files) != len(sharp):
                continue
            for f, s in zip(files, sharp):
                if not isinstance(f, str) or isinstance(s, bool):
                    continue
                name = Path(f).name
                if not name or name.startswith("."):
                    continue
                p = day_dir / name
                if p.is_file():
                    cands[phase].append((float(s), p))
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    for phase in ("plateau", "lit"):
        if cands[phase]:
            return max(cands[phase], key=lambda c: c[0])[1]
    return None


def _items(reg):
    items = [i for i in (reg.get("items") or {}).values() if isinstance(i, dict)]

    def key(i):
        s = str(i.get("id", ""))
        return (0, int(s), s) if s.isdigit() else (1, 0, s)
    return sorted(items, key=key)


def _active(reg):
    return [i for i in _items(reg) if i.get("state") != "gone"]


def _jpeg(im, q=90):
    b = io.BytesIO()
    im.save(b, "JPEG", quality=q)
    return b.getvalue()


def _overview(today: Path, reg) -> Image.Image:
    im = Image.open(today).convert("RGB")
    w, h = im.size
    im = im.resize((max(1, w // 2), max(1, h // 2)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    f = annotate.font(11)
    for gx in range(0, w, GRID):
        d.line([(gx / 2, 0), (gx / 2, im.size[1])], fill=(255, 255, 255), width=1)
        d.text((gx / 2 + 2, 2), str(gx), font=f, fill=(255, 255, 0), stroke_width=1,
               stroke_fill=(0, 0, 0))
    for gy in range(GRID, h, GRID):
        d.line([(0, gy / 2), (im.size[0], gy / 2)], fill=(255, 255, 255), width=1)
        d.text((2, gy / 2 + 2), str(gy), font=f, fill=(255, 255, 0), stroke_width=1,
               stroke_fill=(0, 0, 0))
    dots = []
    for it in _active(reg):
        try:
            dots.append({"id": it["id"], "x": float(it["x"]) / 2, "y": float(it["y"]) / 2,
                         "needs_owner": it.get("needs_owner")})
        except (KeyError, TypeError, ValueError):
            pass
    out = annotate.draw_dots(_jpeg(im, 92), dots)
    return Image.open(io.BytesIO(out)).convert("RGB")


def _crop(im: Image.Image, x, y) -> Image.Image:
    w, h = im.size
    c = min(CROP, w, h)
    left = int(round(min(max(x - c / 2, 0), w - c)))
    top = int(round(min(max(y - c / 2, 0), h - c)))
    cr = im.crop((left, top, left + c, top + c))
    cx, cy = x - left, y - top
    if 0 <= cx < c and 0 <= cy < c:
        d = ImageDraw.Draw(cr)
        r = 22
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255), width=1)
    return cr.resize((c * 2, c * 2), Image.LANCZOS)


def _placeholder(size) -> Image.Image:
    im = Image.new("RGB", size, (128, 128, 128))
    ImageDraw.Draw(im).text((size[0] // 2 - 60, size[1] // 2), "no yesterday",
                            font=annotate.font(24), fill=(255, 255, 255))
    return im


def build_inputs(today: Path, yesterday: Optional[Path], reg: dict, workdir: Path) -> list:
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    paths = []
    p = workdir / "overview.jpg"
    _overview(Path(today), reg).save(p, "JPEG", quality=90)
    paths.append(p)
    tim = Image.open(today).convert("RGB")
    yim = Image.open(yesterday).convert("RGB") if yesterday else None
    for it in _active(reg):
        try:
            x, y = float(it["x"]), float(it["y"])
        except (KeyError, TypeError, ValueError):
            continue
        left = _crop(tim, x, y)
        right = _crop(yim, x, y) if yim else _placeholder(left.size)
        sheet = Image.new("RGB", (left.size[0] * 2, left.size[1]))
        sheet.paste(left, (0, 0))
        sheet.paste(right, (left.size[0], 0))
        q = workdir / ("item-%s.jpg" % it["id"])
        sheet.save(q, "JPEG", quality=90)
        paths.append(q)
    return paths


def build_prompt(reg: dict, files: list) -> str:
    names = {Path(f).name for f in files}
    lines = []
    for it in _items(reg):
        fn = "item-%s.jpg" % it.get("id")
        if fn in names:
            lines.append("- id %s: last state %s, stalk %s, file %s" % (
                it.get("id"), it.get("state"), it.get("stalk") or "?", fn))
    return (
        "You are inspecting photos of Heliamphora flowers and buds in a terrarium. "
        "The files are in the current working directory; Read each of them.\n\n"
        "overview.jpg: today's full frame at 50% scale, tracked items marked by numbered "
        "dots, with a 100 px grid labelled in FULL-resolution pixel coordinates.\n"
        "item-<id>.jpg: a 400x400 crop around one tracked item, today on the left and "
        "yesterday on the right (both 2x upscaled; a grey panel means no yesterday).\n\n"
        "Tracked items:\n" + "\n".join(lines) + "\n\n"
        "Judge each item's state by SHAPE, not colour: closed and pointed = bud; tepals "
        "separating = opening; spread = open; limp or shrivelled = fading; absent = gone; "
        "covered or not visible = hidden. Allowed states: bud, opening, open, fading, gone, "
        "hidden.\n"
        "Colour is unreliable under the pink LEDs, and pink does NOT mean old. "
        "Bends and joints on a stalk are not buds.\n"
        "Report a confidence between 0 and 1 for every item. x and y are full-resolution "
        "pixel coordinates of the item in today's frame.\n"
        "List new flower candidates only if they are clearly a Heliamphora flower or bud.\n\n"
        "Answer ONLY with JSON of exactly this shape, no other text:\n"
        '{"items":[{"id","state","confidence","x","y"}],'
        '"new":[{"state","confidence","x","y","note"}]}\n')


class VisionError(Exception):
    pass


def run_claude(prompt: str, workdir, timeout=config.VISION_TIMEOUT_S) -> str:
    env = dict(os.environ)
    for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
        env.pop(k, None)
    cmd = [config.CLAUDE_BIN, "-p", prompt, "--output-format", "json",
           "--tools", "Read", "--allowedTools", "Read",
           "--permission-mode", "dontAsk", "--strict-mcp-config",
           "--disable-slash-commands"]
    try:
        p = subprocess.run(cmd, cwd=str(workdir), env=env, capture_output=True,
                           text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise VisionError("claude timed out")
    except OSError as e:
        raise VisionError("claude not runnable: %s" % e)
    if p.returncode != 0:
        raise VisionError("claude exit %s" % p.returncode)
    try:
        out = json.loads(p.stdout)
    except ValueError:
        raise VisionError("claude output not JSON")
    if not isinstance(out, dict) or out.get("is_error"):
        raise VisionError("claude reported an error")
    res = out.get("result")
    if not isinstance(res, str):
        raise VisionError("claude result missing")
    return res


def _first_object(text: str):
    start = text.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            c = text[i]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except ValueError:
                        break
        start = text.find("{", start + 1)
    return None


def parse_result(text, known_ids) -> dict:
    if not isinstance(text, str):
        raise VisionError("no text")
    obj = _first_object(text.replace("```json", " ").replace("```", " "))
    if not isinstance(obj, dict):
        raise VisionError("no JSON object in answer")
    items, new = obj.get("items"), obj.get("new")
    if not isinstance(items, list) or not isinstance(new, list):
        raise VisionError("items/new missing")
    items = [i for i in items if isinstance(i, dict) and i.get("id") in known_ids]
    return {"items": items, "new": new}


def _geometry_of(day_dir: Path, frame: Path):
    try:
        for fr in json.loads((day_dir / "day.json").read_text())["frames"]:
            if any(Path(f).name == frame.name for f in fr.get("files", [])):
                return fr.get("geometry")
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        pass
    return None


def _day_dir(root, d):
    return Path(root) / "frames" / d.strftime("%Y/%m/%d")


def _hconf(it):
    try:
        return float(it["history"][-1]["confidence"])
    except (KeyError, IndexError, TypeError, ValueError):
        return 0.0


def _summary(before, after, result):
    lines = []
    for r in result["items"]:
        iid = r.get("id")
        b, a = before["items"].get(iid), after["items"].get(iid)
        if not b or not a:
            continue
        who = "%s %s" % (iid, b.get("label") or "")
        if b.get("stalk"):
            who += " (%s)" % b["stalk"]
        conf = r.get("confidence")
        conf = float(conf) if isinstance(conf, (int, float)) else 0.0
        if a.get("needs_owner") and not b.get("needs_owner") or \
                (isinstance(conf, (int, float)) and conf < config.CONFIDENT):
            lines.append("%s: unsure (%.2f) \u2014 needs you" % (iid, float(conf)))
        else:
            lines.append("%s: %s \u2192 %s (%.2f)" % (who.strip(), b.get("state"),
                                                       a.get("state"), float(conf)))
    for iid in sorted(set(after["items"]) - set(before["items"])):
        it = after["items"][iid]
        lines.append("%s: new %s candidate (%.2f) \u2014 needs you" % (
            iid, it.get("state"), _hconf(it)))
    return lines


def daily(date, root, runner=run_claude, registry_path=None) -> dict:
    root = Path(root)
    regp = Path(registry_path) if registry_path else root / "registry.json"
    ds = date.isoformat()
    status_path = root / "status" / ("vision-%s.json" % ds)

    def finish(status, why="", summary=(), pending=()):
        st = {"status": status, "why": why, "summary": list(summary),
              "pending": list(pending)}
        storage.write_atomic(status_path, (json.dumps(st, indent=2) + "\n").encode())
        return st

    tdir = _day_dir(root, date)
    today = pick_best(tdir)
    if today is None:
        return finish("no_frame", "no usable frame today")
    work = None
    try:
        reg = registry.load(regp)
        geom = _geometry_of(tdir, today)
        ydir = _day_dir(root, date - timedelta(days=1))
        yest = pick_best(ydir)
        if yest is not None and _geometry_of(ydir, yest) != geom:
            yest = None
        tmpbase = root / "tmp"
        try:
            tmpbase.mkdir(parents=True, exist_ok=True)
        except OSError:
            tmpbase = None
        work = Path(tempfile.mkdtemp(prefix="vision-", dir=str(tmpbase) if tmpbase else None))
        files = build_inputs(today, yest, reg, work)
        prompt = build_prompt(reg, files)
        text = runner(prompt, work)
        result = parse_result(text, set(reg.get("items", {})))
        try:
            after = registry.apply_vision(reg, ds, result, geom)
        except ValueError as e:
            if "already applied" in str(e):
                return finish("already_done", "already applied for %s" % ds)
            raise VisionError("apply_vision: %s" % e)
        except TypeError as e:
            raise VisionError("apply_vision: %s" % e)
        pending = [i for i, it in sorted(after["items"].items())
                   if it.get("needs_owner")]
        try:
            summ = _summary(reg, after, result)
        except Exception as e:
            summ = ["summary unavailable: %s" % type(e).__name__]
        if after.get("runs") and after["runs"][-1].get("status") == "geometry_changed":
            summ.insert(0, "camera geometry changed \u2014 every item needs you")
        registry.save(regp, after)
        note = ""
        if pending:
            try:
                dots = [it for it in after["items"].values() if it.get("state") != "gone"]
                img = annotate.draw_dots(today.read_bytes(), dots, show_pending=True)
                storage.write_atomic(root / "status" / ("checkin-%s.jpg" % ds), img)
            except Exception as e:
                note = "checkin image failed: %s" % str(e)[:150]
        return finish("ok", note, summ, pending)
    except VisionError as e:
        return finish("vision_failed", str(e)[:200])
    except Exception as e:  # never leave the registry half-written
        return finish("vision_failed", "%s: %s" % (type(e).__name__, str(e)[:150]))
    finally:
        if work is not None:
            shutil.rmtree(work, ignore_errors=True)


def main() -> int:
    root = Path(config.ARCHIVE_ROOT)
    try:
        st = daily(_date.today(), root)
        line = "%s %s %s pending=%s" % (_date.today().isoformat(), st["status"],
                                        st.get("why", ""), ",".join(st["pending"]))
    except BaseException as e:
        line = "%s error %s: %s" % (_date.today().isoformat(), type(e).__name__, e)
    try:
        lp = root / "logs" / "vision.log"
        lp.parent.mkdir(parents=True, exist_ok=True)
        with open(lp, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
