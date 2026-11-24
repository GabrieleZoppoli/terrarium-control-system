"""Flower registry: what the daily vision check tracks, plus the owner CLI.

Registry file: {"geometry", "items": {id: Item}, "runs": [{"date","status","note"}]}.
Contains coordinates and labels only, never pixels.
"""
import argparse
import copy
import json
import math
import sys
from pathlib import Path

from timelapse import config, storage

STATES = ("bud", "opening", "open", "fading", "gone", "hidden")


def _empty():
    return {"geometry": "", "items": {}, "runs": []}


def load(path) -> dict:
    """Read the registry; a missing file is an empty registry."""
    p = Path(path)
    if not p.exists():
        return _empty()
    return json.loads(p.read_text())


def save(path, reg) -> None:
    """Atomically write the registry."""
    storage.write_atomic(path, (json.dumps(reg, indent=2, sort_keys=True) + "\n").encode())


def _ensure_next(reg) -> None:
    """Old registries lack next_id: start it at max existing id + 1."""
    if "next_id" not in reg:
        nums = [int(i[1:]) for i in reg["items"] if i[:1] == "f" and i[1:].isdigit()]
        reg["next_id"] = max(nums, default=0) + 1


def _alloc_id(reg) -> str:
    """Allocate a never-reused id from the persistent counter."""
    _ensure_next(reg)
    iid = "f%d" % reg["next_id"]
    reg["next_id"] += 1
    return iid


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _check(cond, msg):
    if not cond:
        raise ValueError("invalid vision result: " + msg)


def _validate_entry(e, need_id):
    _check(isinstance(e, dict), "entry is not an object")
    keys = ("state", "confidence", "x", "y") + (("id",) if need_id else ())
    for k in keys:
        _check(k in e, "missing key %r" % k)
    _check(e["state"] in STATES, "bad state %r" % (e["state"],))
    c = e["confidence"]
    _check(_num(c) and math.isfinite(c) and 0 <= c <= 1, "bad confidence %r" % (c,))
    for k in ("x", "y"):
        _check(isinstance(e[k], int) and not isinstance(e[k], bool) and e[k] >= 0,
               "bad %s %r" % (k, e[k]))


def _validate(result):
    _check(isinstance(result, dict), "result is not an object")
    for e in result.get("items", []):
        _validate_entry(e, True)
    for e in result.get("new", []):
        _validate_entry(e, False)


def _new_item(iid, kind, label, stalk, state, x, y, date, confirmed, needs_owner,
              conf, source):
    return {"id": iid, "kind": kind, "label": label, "stalk": stalk, "state": state,
            "x": x, "y": y, "first_seen": date,
            "opened_on": date if state == "open" else None,
            "ended_on": date if state == "gone" else None,
            "confirmed": confirmed, "needs_owner": needs_owner, "streak": 0,
            "history": [{"date": date, "state": state, "confidence": conf,
                         "source": source}]}


def _set_state(item, state, date):
    item["state"] = state
    if state == "open" and not item.get("opened_on"):
        item["opened_on"] = date
    if state == "gone":
        item["ended_on"] = date


def apply_vision(reg, date, result, geometry) -> dict:
    """Merge one day's vision result into a copy of reg (input is not mutated)."""
    _validate(result)
    if any(r.get("date") == date and r.get("status") == "ok"
           for r in reg.get("runs", [])):
        raise ValueError("already applied for %s" % date)
    out = copy.deepcopy(reg)
    _ensure_next(out)
    if out.get("geometry") and out["geometry"] != geometry:
        for item in out["items"].values():
            item["needs_owner"] = True
        out["runs"].append({"date": date, "status": "geometry_changed",
                            "note": "%s -> %s" % (out["geometry"], geometry)})
        return out
    out["geometry"] = geometry
    for r in result.get("items", []):
        item = out["items"].get(r.get("id"))
        if item is None:
            continue
        conf = r["confidence"]
        if conf >= config.CONFIDENT:
            _set_state(item, r["state"], date)
            item["x"], item["y"] = r["x"], r["y"]
            item["streak"] += 1
            item["history"].append({"date": date, "state": r["state"],
                                    "confidence": conf, "source": "vision"})
        else:
            item["needs_owner"] = True
            item["streak"] = 0
    for c in result.get("new", []):
        iid = _alloc_id(out)
        out["items"][iid] = _new_item(iid, "flower", "Heliamphora", "", c["state"],
                                      c["x"], c["y"], date, False, True,
                                      c["confidence"], "vision")
    out["runs"].append({"date": date, "status": "ok", "note": ""})
    return out


def is_public(item) -> bool:
    """Public if confirmed or confidently seen PUBLIC_STREAK times; never if needs_owner."""
    if item.get("needs_owner"):
        return False
    return bool(item.get("confirmed")) or item.get("streak", 0) >= config.PUBLIC_STREAK


def _today():
    import datetime
    return datetime.date.today().isoformat()


def _owner(item, state=None):
    item["confirmed"], item["needs_owner"] = True, False
    if state is not None:
        _set_state(item, state, _today())
    item["history"].append({"date": _today(), "state": item["state"],
                            "confidence": 1.0, "source": "owner"})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="timelapse.registry")
    ap.add_argument("--path", default=config.REGISTRY_PATH)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    for name in ("confirm", "drop"):
        sub.add_parser(name).add_argument("id")
    s = sub.add_parser("set")
    s.add_argument("id")
    s.add_argument("state", choices=STATES)
    m = sub.add_parser("move")
    m.add_argument("id")
    m.add_argument("x", type=int)
    m.add_argument("y", type=int)
    sub.add_parser("geometry").add_argument("geometry")
    a = sub.add_parser("add")
    a.add_argument("kind")
    a.add_argument("state", choices=STATES)
    a.add_argument("x", type=int)
    a.add_argument("y", type=int)
    a.add_argument("label")
    a.add_argument("--stalk", default="")
    sd = sub.add_parser("seed")
    sd.add_argument("file")
    sd.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)

    reg = load(args.path)
    items = reg["items"]
    _ensure_next(reg)
    if args.cmd == "list":
        for i, v in sorted(items.items(), key=lambda kv: int(kv[0][1:]) if kv[0][1:].isdigit() else 0):
            print("%s %s (%d,%d) %s %s%s" % (
                i, v["state"], v["x"], v["y"], v["stalk"],
                "confirmed" if v["confirmed"] else "unconfirmed",
                " needs_owner" if v["needs_owner"] else ""))
        return 0
    if args.cmd == "seed":
        if items and not args.force:
            print("registry not empty; use --force to overwrite", file=sys.stderr)
            return 1
        save(args.path, json.loads(Path(args.file).read_text()))
        return 0
    if args.cmd == "geometry":
        reg["runs"].append({"date": _today(), "status": "owner",
                            "note": "geometry set: %s -> %s" % (reg.get("geometry", ""), args.geometry)})
        reg["geometry"] = args.geometry
    elif args.cmd == "add":
        iid = _alloc_id(reg)
        items[iid] = _new_item(iid, args.kind, args.label, args.stalk, args.state,
                               args.x, args.y, _today(), True, False, 1.0, "owner")
        print(iid)
    else:
        if args.id not in items:
            print("unknown id %s" % args.id, file=sys.stderr)
            return 1
        item = items[args.id]
        if args.cmd == "confirm":
            _owner(item)
        elif args.cmd == "set":
            _owner(item, args.state)
        elif args.cmd == "move":
            item["x"], item["y"] = args.x, args.y
            _owner(item)
        elif args.cmd == "drop":
            del items[args.id]
    save(args.path, reg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
