import json, math, os, tempfile, time, unittest
from datetime import datetime

from timelapse import conditions as C
from timelapse.conditions import LightWindow

REAL = {"payload": {"photo_light_on": 408, "photo_light_off": 1182,
                    "photo_midday_up": 707, "photo_midday_down": 883}}


class LightWindowTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.p = os.path.join(self.d.name, "global.json")

    def tearDown(self):
        self.d.cleanup()

    def write(self, obj, raw=None):
        with open(self.p, "w") as f:
            f.write(raw if raw is not None else json.dumps(obj))

    def payload(self, **kw):
        pl = dict(REAL["payload"])
        pl.update(kw)
        return {"payload": pl}

    def test_real_values(self):
        self.write(REAL)
        self.assertEqual(C.light_window(self.p), LightWindow(408, 1182, 737, 883))

    def test_float_minutes_ok(self):
        self.write(self.payload(photo_light_on=408.5))
        self.assertEqual(C.light_window(self.p).on, 408.5)

    def test_missing_file(self):
        self.assertIsNone(C.light_window(self.p))

    def test_garbage(self):
        self.write(None, raw="{not json")
        self.assertIsNone(C.light_window(self.p))

    def test_non_dict_shapes(self):
        for raw in ("[]", "null", '{"payload": 5}', "{}"):
            self.write(None, raw=raw)
            self.assertIsNone(C.light_window(self.p), raw)

    def test_missing_key(self):
        o = self.payload()
        del o["payload"]["photo_midday_up"]
        self.write(o)
        self.assertIsNone(C.light_window(self.p))

    def test_string_value(self):
        self.write(self.payload(photo_light_on="408"))
        self.assertIsNone(C.light_window(self.p))

    def test_bool_and_nan_rejected(self):
        self.write(self.payload(photo_light_on=True))
        self.assertIsNone(C.light_window(self.p))
        self.write(None, raw=json.dumps(self.payload()).replace("408", "NaN"))
        self.assertIsNone(C.light_window(self.p))

    def test_bad_ordering(self):
        self.write(self.payload(photo_midday_down=1300))
        self.assertIsNone(C.light_window(self.p))
        self.write(self.payload(photo_midday_down=730))  # plateau_end <= start
        self.assertIsNone(C.light_window(self.p))

    def test_old_mtime(self):
        self.write(REAL)
        old = time.time() - 7200
        os.utime(self.p, (old, old))
        self.assertIsNone(C.light_window(self.p))


class PhaseTests(unittest.TestCase):
    W = LightWindow(408, 1182, 737, 883)

    def ph(self, h, m):
        return C.phase(datetime(2026, 11, 24, h, m), self.W)

    def test_phases(self):
        self.assertEqual(self.ph(6, 47), "night")
        self.assertEqual(self.ph(6, 48), "lit")
        self.assertEqual(self.ph(12, 17), "plateau")
        self.assertEqual(self.ph(12, 16), "lit")
        self.assertEqual(self.ph(14, 43), "lit")
        self.assertEqual(self.ph(19, 41), "lit")
        self.assertEqual(self.ph(19, 42), "night")
        self.assertEqual(self.ph(0, 0), "night")

    def test_aware_datetime(self):
        from datetime import timezone
        self.assertEqual(C.phase(datetime(2026, 11, 24, 12, 30, tzinfo=timezone.utc), self.W), "plateau")


def gate(**kw):
    g = {"ok": True, "reason": "ok", "last_not_ok_at": 0, "now": 1000}
    g.update(kw)
    return g


class GateTests(unittest.TestCase):
    def test_ok(self):
        self.assertIsNone(C.gate_check(gate(), 1000))
        self.assertIsNone(C.gate_check(gate(last_not_ok_at=400.0), 1000))  # exactly 600

    def test_after_private(self):
        self.assertEqual(C.gate_check(gate(last_not_ok_at=500), 1000), "after_private")

    def test_not_ok(self):
        self.assertEqual(C.gate_check(gate(ok=False, reason="doors_open"), 1000), "gate_doors_open")

    def test_not_ok_without_reason(self):
        self.assertEqual(C.gate_check(gate(ok=False, reason=None), 1000), "gate_invalid")

    def test_unreachable(self):
        self.assertEqual(C.gate_check(None, 1000), "gate_unreachable")

    def test_fail_closed(self):
        bad = [
            {}, [], "x",
            {"ok": True},
            {"last_not_ok_at": 0},
            gate(ok=1), gate(ok="true"), gate(ok=None),
            gate(last_not_ok_at=float("nan")),
            gate(last_not_ok_at=float("inf")),
            gate(last_not_ok_at=-float("inf")),
            gate(last_not_ok_at=None), gate(last_not_ok_at="0"),
            gate(last_not_ok_at=True),
            gate(last_not_ok_at=2000),  # future
        ]
        for g in bad:
            self.assertEqual(C.gate_check(g, 1000), "gate_invalid", g)

    def test_bad_now(self):
        self.assertEqual(C.gate_check(gate(), float("nan")), "gate_invalid")

    def test_missing_key_when_not_ok(self):
        self.assertEqual(C.gate_check({"ok": False}, 1000), "gate_invalid")


class MistTests(unittest.TestCase):
    def test_misting(self):
        self.assertEqual(C.mist_check({"mister": True}, None, 1000), "misting")

    def test_unreachable(self):
        self.assertEqual(C.mist_check(None, None, 1000), "conditions_unreachable")

    def test_invalid_conditions(self):
        for c in ({}, {"mister": None}, {"mister": 0}, {"mister": "false"}, [], "x"):
            self.assertEqual(C.mist_check(c, None, 1000), "conditions_invalid", c)

    def test_recent(self):
        self.assertEqual(C.mist_check({"mister": False}, 800, 1000), "mist_recent")

    def test_quiet(self):
        self.assertIsNone(C.mist_check({"mister": False}, 600, 1000))
        self.assertIsNone(C.mist_check({"mister": False}, None, 1000))

    def test_bad_last_mist(self):
        for t in (float("nan"), float("inf"), "5", True):
            self.assertEqual(C.mist_check({"mister": False}, t, 1000), "conditions_invalid", t)

    def test_future_mist_is_recent(self):
        self.assertEqual(C.mist_check({"mister": False}, 1500, 1000), "mist_recent")


if __name__ == "__main__":
    unittest.main()
