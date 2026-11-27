import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from timelapse import registry

GEO = "1168x1080+176+0/rot180"
SEED = Path(registry.__file__).parent / "seed_2026-11-24.json"


def seeded():
    return json.loads(SEED.read_text())


def vis(items=(), new=()):
    return {"items": list(items), "new": list(new)}


def it(i, state, conf, x=1, y=2):
    return {"id": i, "state": state, "confidence": conf, "x": x, "y": y}


class ApplyVision(unittest.TestCase):
    def test_load_missing_is_empty(self):
        reg = registry.load("/nonexistent/registry.json")
        self.assertEqual(reg["items"], {})
        self.assertEqual(reg["runs"], [])

    def test_save_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "sub", "r.json")
            registry.save(p, seeded())
            self.assertEqual(registry.load(p), seeded())

    def test_seed_shape(self):
        reg = seeded()
        self.assertEqual(reg["geometry"], GEO)
        self.assertEqual(sorted(reg["items"]), ["f1", "f2", "f3", "f4", "f5"])
        self.assertEqual(reg["items"]["f4"]["opened_on"], "2026-11-24")
        self.assertIsNone(reg["items"]["f1"]["opened_on"])

    def test_geometry_change_flags_all_no_state_change(self):
        out = registry.apply_vision(seeded(), "2026-11-25",
                                    vis([it("f1", "open", 0.99)]), "other/geom")
        for i in out["items"].values():
            self.assertTrue(i["needs_owner"])
        self.assertEqual(out["items"]["f1"]["state"], "bud")

    def test_confident_updates_state_position_streak(self):
        out = registry.apply_vision(seeded(), "2026-11-25",
                                    vis([it("f1", "opening", 0.9, 471, 320)]), GEO)
        f = out["items"]["f1"]
        self.assertEqual((f["state"], f["x"], f["y"], f["streak"]), ("opening", 471, 320, 1))
        self.assertEqual(f["history"][-1]["source"], "vision")
        self.assertEqual(f["history"][-1]["date"], "2026-11-25")

    def test_opened_on_set_on_first_open_only(self):
        out = registry.apply_vision(seeded(), "2026-11-25", vis([it("f2", "open", 0.9)]), GEO)
        self.assertEqual(out["items"]["f2"]["opened_on"], "2026-11-25")
        out = registry.apply_vision(out, "2026-11-26", vis([it("f2", "open", 0.9)]), GEO)
        self.assertEqual(out["items"]["f2"]["opened_on"], "2026-11-25")

    def test_gone_sets_ended_on(self):
        out = registry.apply_vision(seeded(), "2026-11-25", vis([it("f4", "gone", 0.95)]), GEO)
        self.assertEqual(out["items"]["f4"]["ended_on"], "2026-11-25")

    def test_low_confidence_keeps_confirmed_item_public(self):
        reg = seeded()
        reg["items"]["f1"].update(confirmed=True, needs_owner=False, streak=2)
        out = registry.apply_vision(reg, "2026-11-25", vis([it("f1", "open", 0.5, 9, 9)]), GEO)
        f = out["items"]["f1"]
        self.assertEqual((f["state"], f["x"], f["needs_owner"], f["streak"]), ("bud", 470, False, 0))
        self.assertTrue(registry.is_public(f))

    def test_low_confidence_keeps_state_flags_owner(self):
        reg = seeded()
        reg["items"]["f1"].update(confirmed=False, streak=2)
        out = registry.apply_vision(reg, "2026-11-25", vis([it("f1", "open", 0.5, 9, 9)]), GEO)
        f = out["items"]["f1"]
        self.assertEqual((f["state"], f["x"], f["needs_owner"], f["streak"]), ("bud", 470, True, 0))

    def test_unknown_id_ignored(self):
        out = registry.apply_vision(seeded(), "2026-11-25", vis([it("f99", "open", 0.99)]), GEO)
        self.assertNotIn("f99", out["items"])
        self.assertEqual(len(out["items"]), 5)

    def test_new_candidates_added(self):
        out = registry.apply_vision(seeded(), "2026-11-25", vis(new=[
            {"state": "bud", "confidence": 0.9, "x": 5, "y": 6, "note": "n"},
            {"state": "bud", "confidence": 0.3, "x": 7, "y": 8, "note": ""}]), GEO)
        self.assertEqual(sorted(out["items"])[-2:], ["f6", "f7"])
        for i in ("f6", "f7"):
            self.assertFalse(out["items"][i]["confirmed"])
            self.assertTrue(out["items"][i]["needs_owner"])

    def test_no_mutation_and_run_record(self):
        reg = seeded()
        before = json.dumps(reg, sort_keys=True)
        out = registry.apply_vision(reg, "2026-11-25", vis([it("f1", "opening", 0.9)]), GEO)
        self.assertEqual(json.dumps(reg, sort_keys=True), before)
        self.assertEqual(out["runs"][-1], {"date": "2026-11-25", "status": "ok", "note": ""})

    def test_duplicate_date_raises(self):
        out = registry.apply_vision(seeded(), "2026-11-25", vis(), GEO)
        with self.assertRaisesRegex(ValueError, "already applied for 2026-11-25"):
            registry.apply_vision(out, "2026-11-25", vis(), GEO)


class Validation(unittest.TestCase):
    def bad(self, result):
        reg = seeded()
        before = json.dumps(reg, sort_keys=True)
        with self.assertRaises(ValueError):
            registry.apply_vision(reg, "2026-11-25", result, GEO)
        self.assertEqual(json.dumps(reg, sort_keys=True), before)

    def test_bad_state(self):
        self.bad(vis([it("f1", "blooming", 0.9)]))

    def test_nan_confidence(self):
        self.bad(vis([it("f1", "open", float("nan"))]))

    def test_out_of_range_confidence(self):
        self.bad(vis([it("f1", "open", 1.5)]))
        self.bad(vis([it("f1", "open", -0.1)]))

    def test_bool_rejected(self):
        self.bad(vis([it("f1", "open", True)]))
        self.bad(vis([it("f1", "open", 0.9, True, 2)]))

    def test_bad_coords(self):
        self.bad(vis([it("f1", "open", 0.9, -1, 2)]))
        self.bad(vis([it("f1", "open", 0.9, 1.5, 2)]))

    def test_missing_key(self):
        e = it("f1", "open", 0.9)
        del e["confidence"]
        self.bad(vis([e]))

    def test_bad_new_candidate(self):
        self.bad(vis([it("f1", "opening", 0.9)],
                     new=[{"state": "bud", "confidence": float("nan"), "x": 1, "y": 2}]))
        self.bad(vis(new=[{"state": "weird", "confidence": 0.9, "x": 1, "y": 2}]))
        self.bad(vis(new=[{"state": "bud", "confidence": 0.9, "x": 1}]))


class IdsAndGeometry(unittest.TestCase):
    def test_ids_never_reused_vision(self):
        reg = seeded()
        reg["next_id"] = 6
        del reg["items"]["f5"]
        out = registry.apply_vision(reg, "2026-11-25", vis(new=[
            {"state": "bud", "confidence": 0.9, "x": 5, "y": 6}]), GEO)
        self.assertIn("f6", out["items"])
        self.assertNotIn("f5", out["items"])
        self.assertEqual(out["next_id"], 7)

    def test_drop_then_add_cli_new_id(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.json")
            registry.save(p, seeded())  # old-style: no next_id
            Cli().run_cli(p, "drop", "f5")
            _, out = Cli().run_cli(p, "add", "flower", "bud", "1", "2", "H")
            self.assertEqual(out.strip(), "f6")
            self.assertEqual(registry.load(p)["next_id"], 7)

    def test_mismatch_run_record_and_retry(self):
        out = registry.apply_vision(seeded(), "2026-11-25", vis(), "new/geom")
        self.assertEqual(out["runs"][-1], {"date": "2026-11-25",
                         "status": "geometry_changed", "note": GEO + " -> new/geom"})
        self.assertEqual(out["geometry"], GEO)
        again = registry.apply_vision(out, "2026-11-25", vis(), GEO)
        self.assertEqual(again["runs"][-1]["status"], "ok")

    def test_geometry_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.json")
            registry.save(p, seeded())
            Cli().run_cli(p, "geometry", "1000x900+0+0/rot180")
            r = registry.load(p)
            self.assertEqual(r["geometry"], "1000x900+0+0/rot180")
            self.assertEqual(len(r["items"]), 5)
            self.assertEqual(r["runs"][-1]["status"], "owner")


class Public(unittest.TestCase):
    def test_rules(self):
        b = {"confirmed": False, "needs_owner": False, "streak": 0}
        self.assertFalse(registry.is_public(b))
        self.assertTrue(registry.is_public({**b, "confirmed": True}))
        self.assertTrue(registry.is_public({**b, "streak": 3}))
        self.assertFalse(registry.is_public({**b, "streak": 2}))
        self.assertFalse(registry.is_public({**b, "confirmed": True, "needs_owner": True}))


class Cli(unittest.TestCase):
    def run_cli(self, p, *args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = registry.main(["--path", p, *args])
        return rc, buf.getvalue()

    def test_add_set_list(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.json")
            self.assertEqual(self.run_cli(p, "add", "flower", "bud", "10", "20", "Heliamphora",
                                          "--stalk", "left")[0], 0)
            self.run_cli(p, "set", "f1", "open")
            _, out = self.run_cli(p, "list")
            self.assertIn("f1 open (10,20) left confirmed", out)
            reg = registry.load(p)
            self.assertEqual(reg["items"]["f1"]["history"][-1]["source"], "owner")
            self.assertEqual(reg["items"]["f1"]["opened_on"] is not None, True)

    def test_confirm_move_drop(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.json")
            reg = seeded()
            reg["items"]["f1"].update(confirmed=False, needs_owner=True)
            registry.save(p, reg)
            self.run_cli(p, "confirm", "f1")
            self.run_cli(p, "move", "f1", "1", "2")
            self.run_cli(p, "drop", "f2")
            r = registry.load(p)
            self.assertTrue(r["items"]["f1"]["confirmed"])
            self.assertFalse(r["items"]["f1"]["needs_owner"])
            self.assertEqual((r["items"]["f1"]["x"], r["items"]["f1"]["y"]), (1, 2))
            self.assertNotIn("f2", r["items"])

    def test_seed_refuses_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.json")
            self.assertEqual(self.run_cli(p, "seed", str(SEED))[0], 0)
            self.assertEqual(len(registry.load(p)["items"]), 5)
            self.run_cli(p, "drop", "f1")
            self.assertNotEqual(self.run_cli(p, "seed", str(SEED))[0], 0)
            self.assertEqual(len(registry.load(p)["items"]), 4)
            self.assertEqual(self.run_cli(p, "seed", str(SEED), "--force")[0], 0)
            self.assertEqual(len(registry.load(p)["items"]), 5)


if __name__ == "__main__":
    unittest.main()
