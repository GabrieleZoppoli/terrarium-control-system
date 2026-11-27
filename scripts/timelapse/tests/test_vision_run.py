import json
import os
import subprocess
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from PIL import Image

from timelapse import registry, vision

D = date(2026, 11, 24)


def _item(iid, state="bud", x=300, y=300):
    return {"id": iid, "kind": "flower", "label": "Heliamphora", "stalk": "centre",
            "state": state, "x": x, "y": y, "first_seen": "2026-11-20",
            "opened_on": None, "ended_on": None, "confirmed": True,
            "needs_owner": False, "streak": 0, "history": []}


def _setup(root, geom="g", reg_geom="g", frame=True):
    root = Path(root)
    if frame:
        d = root / "frames" / "2026" / "11" / "24"
        d.mkdir(parents=True)
        Image.new("RGB", (800, 700), (30, 80, 30)).save(d / "1200.jpg", "JPEG")
        (d / "day.json").write_text(json.dumps({"frames": [
            {"time": "12:00", "files": ["frames/2026/11/24/1200.jpg"], "phase": "plateau",
             "geometry": geom, "sharpness": [5.0]}]}))
    reg = {"geometry": reg_geom, "next_id": 4, "runs": [],
           "items": {"f1": _item("f1"), "f2": {**_item("f2", x=500, y=400), "confirmed": False}}}
    registry.save(root / "registry.json", reg)
    return root / "registry.json"


def _ans(items, new=()):
    return "```json\n" + json.dumps({"items": items, "new": list(new)}) + "\n```"


GOOD = [{"id": "f1", "state": "opening", "confidence": 0.92, "x": 301, "y": 302},
        {"id": "f2", "state": "open", "confidence": 0.55, "x": 500, "y": 400}]


class TestDaily(unittest.TestCase):
    def test_ok(self):
        with tempfile.TemporaryDirectory() as t:
            rp = _setup(t)
            st = vision.daily(D, t, runner=lambda p, w: _ans(GOOD))
            self.assertEqual(st["status"], "ok")
            self.assertEqual(st["pending"], ["f2"])
            self.assertTrue(any("f1 Heliamphora (centre): bud" in s and "opening" in s
                                for s in st["summary"]), st["summary"])
            self.assertTrue(any(s.startswith("f2: unsure (0.55)") for s in st["summary"]))
            self.assertEqual(registry.load(rp)["items"]["f1"]["state"], "opening")
            self.assertTrue((Path(t) / "status" / "checkin-2026-11-24.jpg").exists())
            on_disk = json.loads((Path(t) / "status" / "vision-2026-11-24.json").read_text())
            self.assertEqual(on_disk["status"], "ok")
            self.assertEqual(list((Path(t) / "tmp").iterdir()), [])
            sp = Path(t) / "status" / "vision-2026-11-24.json"
            before = sp.read_bytes()
            st2 = vision.daily(D, t, runner=lambda p, w: _ans(GOOD))
            self.assertEqual(st2["status"], "ok")
            self.assertEqual(sp.read_bytes(), before)
            self.assertEqual(json.loads(sp.read_text())["status"], "ok")
            self.assertTrue((Path(t) / "status" / "checkin-2026-11-24.jpg").exists())

    def test_unsure_confirmed_item_kept(self):
        with tempfile.TemporaryDirectory() as t:
            rp = _setup(t)
            ans = [{"id": "f1", "state": "open", "confidence": 0.5, "x": 9, "y": 9}]
            st = vision.daily(D, t, runner=lambda p, w: _ans(ans))
            self.assertEqual(st["pending"], [])
            self.assertIn("f1: unsure (0.50) \u2014 kept as you set it", st["summary"])
            f1 = registry.load(rp)["items"]["f1"]
            self.assertEqual((f1["state"], f1["x"], f1["needs_owner"]), ("bud", 300, False))

    def test_float_and_out_of_frame_coords(self):
        with tempfile.TemporaryDirectory() as t:
            rp = _setup(t)   # frame is 800x700
            ans = [{"id": "f1", "state": "opening", "confidence": 0.92, "x": 470.0, "y": 317.6},
                   {"id": "f2", "state": "open", "confidence": 0.9, "x": 5000, "y": -3.2}]
            st = vision.daily(D, t, runner=lambda p, w: _ans(ans))
            self.assertEqual(st["status"], "ok", st)
            items = registry.load(rp)["items"]
            self.assertEqual((items["f1"]["x"], items["f1"]["y"]), (470, 318))
            self.assertEqual((items["f2"]["x"], items["f2"]["y"]), (799, 0))

    def test_checkin_failure_keeps_ok(self):
        with tempfile.TemporaryDirectory() as t:
            rp = _setup(t)
            from timelapse import annotate
            real = annotate.draw_dots

            def flaky(jpeg, items, show_pending=True):
                if show_pending is True and any(i.get("needs_owner") for i in items):
                    raise RuntimeError("boom")
                return real(jpeg, items, show_pending)
            with mock.patch("timelapse.annotate.draw_dots", side_effect=flaky):
                st = vision.daily(D, t, runner=lambda p, w: _ans(GOOD))
            self.assertEqual(st["status"], "ok")
            self.assertIn("checkin image failed", st["why"])
            self.assertEqual(registry.load(rp)["items"]["f1"]["state"], "opening")

    def test_prose_fails_registry_unchanged(self):
        with tempfile.TemporaryDirectory() as t:
            rp = _setup(t)
            before = rp.read_bytes()
            st = vision.daily(D, t, runner=lambda p, w: "I could not see anything.")
            self.assertEqual(st["status"], "vision_failed")
            self.assertEqual(rp.read_bytes(), before)

    def test_unknown_id_ignored(self):
        with tempfile.TemporaryDirectory() as t:
            rp = _setup(t)
            ans = _ans(GOOD + [{"id": "zz", "state": "open", "confidence": 0.9, "x": 1, "y": 1}])
            st = vision.daily(D, t, runner=lambda p, w: ans)
            self.assertEqual(st["status"], "ok")
            self.assertNotIn("zz", registry.load(rp)["items"])

    def test_invalid_state_fails(self):
        with tempfile.TemporaryDirectory() as t:
            rp = _setup(t)
            before = rp.read_bytes()
            bad = [{"id": "f1", "state": "blooming", "confidence": 0.9, "x": 1, "y": 1}]
            st = vision.daily(D, t, runner=lambda p, w: _ans(bad))
            self.assertEqual(st["status"], "vision_failed")
            self.assertEqual(rp.read_bytes(), before)

    def test_timeout(self):
        def boom(p, w):
            raise vision.VisionError("claude timed out")
        with tempfile.TemporaryDirectory() as t:
            rp = _setup(t)
            before = rp.read_bytes()
            st = vision.daily(D, t, runner=boom)
            self.assertEqual(st["status"], "vision_failed")
            self.assertEqual(rp.read_bytes(), before)
            self.assertEqual(list((Path(t) / "tmp").iterdir()), [])

    def test_geometry_mismatch(self):
        with tempfile.TemporaryDirectory() as t:
            rp = _setup(t, geom="new", reg_geom="old")
            st = vision.daily(D, t, runner=lambda p, w: _ans(GOOD))
            self.assertEqual(sorted(st["pending"]), ["f1", "f2"])
            self.assertTrue((Path(t) / "status" / "checkin-2026-11-24.jpg").exists())
            self.assertEqual(registry.load(rp)["items"]["f1"]["state"], "bud")

    def test_no_frame(self):
        with tempfile.TemporaryDirectory() as t:
            _setup(t, frame=False)
            st = vision.daily(D, t, runner=lambda p, w: self.fail("called"))
            self.assertEqual(st["status"], "no_frame")


class TestRunClaude(unittest.TestCase):
    def test_env_and_cmd(self):
        cp = subprocess.CompletedProcess([], 0, stdout=json.dumps({"result": "hi"}), stderr="")
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "k", "ANTHROPIC_AUTH_TOKEN": "x"}):
            with mock.patch("subprocess.run", return_value=cp) as m:
                self.assertEqual(vision.run_claude("p", Path("/tmp")), "hi")
        kw = m.call_args.kwargs
        self.assertNotIn("ANTHROPIC_API_KEY", kw["env"])
        self.assertNotIn("ANTHROPIC_AUTH_TOKEN", kw["env"])
        self.assertEqual(kw["cwd"], "/tmp")
        cmd = m.call_args.args[0]
        self.assertEqual(cmd[1:], ["-p", "p", "--output-format", "json",
                                   "--tools", "Read", "--allowedTools", "Read(./**)",
                                   "--permission-mode", "dontAsk",
                                   "--strict-mcp-config", "--disable-slash-commands",
                                   "--setting-sources", "", "--no-session-persistence"])

    def test_failures(self):
        for cp in (subprocess.CompletedProcess([], 1, stdout="", stderr="e"),
                   subprocess.CompletedProcess([], 0, stdout="nope", stderr=""),
                   subprocess.CompletedProcess([], 0, stdout='{"result":"x","is_error":true}', stderr=""),
                   subprocess.CompletedProcess([], 0, stdout='{}', stderr="")):
            with mock.patch("subprocess.run", return_value=cp):
                with self.assertRaises(vision.VisionError):
                    vision.run_claude("p", Path("/tmp"))
        with mock.patch("subprocess.run",
                        side_effect=subprocess.TimeoutExpired("c", 1)):
            with self.assertRaises(vision.VisionError):
                vision.run_claude("p", Path("/tmp"))


class TestParse(unittest.TestCase):
    def test_prose_around_and_braces_in_strings(self):
        txt = 'ok {"items":[{"id":"f1","note":"a } b"}],"new":[]} done'
        self.assertEqual(vision.parse_result(txt, {"f1"})["items"][0]["id"], "f1")

    def test_float_rounded_and_clamped(self):
        txt = ('{"items":[{"id":"f1","x":470.4,"y":9999.0}],'
               '"new":[{"x":-5.0,"y":10.5}]}')
        r = vision.parse_result(txt, {"f1"}, (800, 700))
        self.assertEqual((r["items"][0]["x"], r["items"][0]["y"]), (470, 699))
        self.assertEqual((r["new"][0]["x"], r["new"][0]["y"]), (0, 10))
        self.assertIsInstance(r["items"][0]["x"], int)

    def test_prompt_demands_integers(self):
        p = vision.build_prompt({"items": {}}, [])
        self.assertIn("integer pixel", p)
        self.assertIn('"x":470,"y":318', p)

    def test_missing_keys(self):
        with self.assertRaises(vision.VisionError):
            vision.parse_result('{"items":[]}', set())


if __name__ == "__main__":
    unittest.main()
