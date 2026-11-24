import io
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

import numpy as np
from PIL import Image

from camgate.config import NO_CROP, Crop
from timelapse import capture
from timelapse.conditions import LightWindow
from timelapse.lossless import LosslessError

NOW_EPOCH = 1_000_000.0
WIN = LightWindow(300, 1200, 600, 900)   # minutes of day
CROP = Crop(1180, 1080, 164, 0)


def make_jpeg():
    rng = np.random.RandomState(1)
    arr = rng.randint(0, 255, (1080, 1920, 3)).astype("uint8")
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="JPEG", quality=80, subsampling=1)
    return buf.getvalue()


GOOD_GATE = {"ok": True, "reason": None, "last_not_ok_at": NOW_EPOCH - 5000, "now": NOW_EPOCH}
SETTLED = dict(GOOD_GATE, now=NOW_EPOCH + 10)   # read after the settle delay


class CaptureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jpeg = make_jpeg()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.gates = [GOOD_GATE, SETTLED]

    def tearDown(self):
        self.tmp.cleanup()

    def deps(self, **kw):
        gates = iter(kw.pop("gates", self.gates))
        d = dict(read_gate=lambda: next(gates),
                 read_conditions=lambda: {"lights": True, "mister": False},
                 read_last_mist=lambda: None,
                 fetch_snapshot=lambda: self.jpeg,
                 light_window=lambda: WIN,
                 load_crop=lambda: CROP,
                 root=self.root,
                 clock=lambda: NOW_EPOCH,
                 sleep=lambda s: None)
        d.update(kw)
        return capture.Deps(**d)

    def files(self):
        return sorted(p for p in self.root.rglob("*.jpg"))

    def run_at(self, hour, minute=0, **kw):
        return capture.capture_once(datetime(2026, 11, 24, hour, minute), self.deps(**kw))

    def sidecar(self):
        return json.loads(next(self.root.rglob("day.json")).read_text())["frames"]

    def test_lit(self):
        r = self.run_at(8)
        self.assertIsNone(r["skipped"])
        self.assertEqual(len(r["saved"]), 1)
        self.assertEqual(len(self.files()), 1)
        e = self.sidecar()[0]
        self.assertEqual(e["phase"], "lit")
        self.assertEqual(e["geometry"], "1168x1080+176+0/rot180")
        self.assertEqual(e["files"], ["frames/2026/11/24/0800.jpg"])
        self.assertEqual(len(e["sharpness"]), 1)
        self.assertGreater(e["sharpness"][0], 0)
        self.assertTrue(e["time"].startswith("2026-11-24T08:00"))
        with Image.open(self.files()[0]) as im:
            self.assertEqual(im.size, (1168, 1080))

    def test_night_archived(self):
        r = self.run_at(2)
        self.assertEqual(len(r["saved"]), 1)
        self.assertEqual(self.sidecar()[0]["phase"], "night")

    def test_plateau_burst(self):
        sleeps = []
        r = self.run_at(12, sleep=sleeps.append)
        self.assertEqual(len(r["saved"]), 3)
        e = self.sidecar()[0]
        self.assertEqual(e["phase"], "plateau")
        self.assertEqual(e["files"], ["frames/2026/11/24/1200-%d.jpg" % i for i in range(3)])
        self.assertEqual(len(e["sharpness"]), 3)
        self.assertEqual(sleeps, [0.3, 0.3, 3.5])

    def test_light_schedule_unknown(self):
        r = self.run_at(8, light_window=lambda: None)
        self.assertEqual(r["skipped"], "light_schedule_unknown")
        self.assertEqual(self.files(), [])

    def test_crop_invalid_and_none(self):
        self.assertEqual(self.run_at(8, load_crop=lambda: None)["skipped"], "crop_invalid")
        self.assertEqual(self.run_at(8, load_crop=lambda: NO_CROP)["skipped"], "crop_none")
        self.assertEqual(self.files(), [])

    def test_crop_outside_frame(self):
        r = self.run_at(8, load_crop=lambda: Crop(1180, 1080, 900, 0))
        self.assertEqual(r["skipped"], "crop_invalid")
        self.assertEqual(self.files(), [])

    def test_non_jpeg_snapshot(self):
        r = self.run_at(8, fetch_snapshot=lambda: b"garbage")
        self.assertEqual(r["skipped"], "crop_invalid")
        self.assertEqual(self.files(), [])

    def test_gate_reasons(self):
        r = self.run_at(8, gates=[None])
        self.assertEqual(r["skipped"], "gate_unreachable")
        g = dict(GOOD_GATE, last_not_ok_at=NOW_EPOCH - 10)
        self.assertEqual(self.run_at(8, gates=[g])["skipped"], "after_private")
        g = dict(GOOD_GATE, ok=False, reason="door_open")
        self.assertEqual(self.run_at(8, gates=[g])["skipped"], "gate_door_open")
        self.assertEqual(self.files(), [])

    def test_mist_reasons(self):
        r = self.run_at(8, read_conditions=lambda: {"mister": True})
        self.assertEqual(r["skipped"], "misting")
        r = self.run_at(8, read_last_mist=lambda: NOW_EPOCH - 60)
        self.assertEqual(r["skipped"], "mist_recent")
        r = self.run_at(8, read_conditions=lambda: None)
        self.assertEqual(r["skipped"], "conditions_unreachable")
        self.assertEqual(self.files(), [])

    def test_influx_failure_fails_closed(self):
        def boom():
            raise OSError("influx down")
        r = self.run_at(8, read_last_mist=boom)
        self.assertEqual(r["skipped"], "mist_unknown")
        self.assertEqual(self.files(), [])

    def test_space(self):
        with mock.patch("timelapse.capture.storage.space_check", return_value="disk_low"):
            r = self.run_at(8)
        self.assertEqual(r["skipped"], "disk_low")
        self.assertEqual(self.files(), [])

    def test_gate_changes_between_checks(self):
        g2 = dict(GOOD_GATE, last_not_ok_at=NOW_EPOCH - 1)
        r = self.run_at(8, gates=[GOOD_GATE, g2])
        self.assertIsNotNone(r["skipped"])
        self.assertEqual(r["saved"], [])
        self.assertEqual(list(self.root.rglob("*")), [])

    def test_gate_not_ok_on_recheck(self):
        g2 = dict(GOOD_GATE, ok=False, reason="door_open")
        r = self.run_at(8, gates=[GOOD_GATE, g2])
        self.assertEqual(r["skipped"], "gate_door_open")
        self.assertEqual(list(self.root.rglob("*")), [])

    def test_gate_unchanged_but_same_value_ok(self):
        g2 = dict(GOOD_GATE, now=NOW_EPOCH + 4)
        r = self.run_at(8, gates=[GOOD_GATE, g2])
        self.assertIsNone(r["skipped"])

    def test_gate_unsettled_discards(self):
        for now2 in (NOW_EPOCH + 1, NOW_EPOCH + 3.4, None, "x"):
            g2 = dict(GOOD_GATE, now=now2)
            r = self.run_at(8, gates=[GOOD_GATE, g2])
            self.assertEqual(r["skipped"], "gate_unsettled", now2)
            self.assertEqual(r["saved"], [])
        self.assertEqual(list(self.root.rglob("*")), [])

    def test_settle_sleep_after_last_snapshot(self):
        order = []
        d = self.deps(sleep=lambda s: order.append(("sleep", s)),
                      fetch_snapshot=lambda: (order.append("snap"), self.jpeg)[1])
        capture.capture_once(datetime(2026, 11, 24, 12, 0), d)
        self.assertEqual(order, ["snap", ("sleep", capture.config.BURST_GAP_S), "snap",
                                 ("sleep", capture.config.BURST_GAP_S), "snap",
                                 ("sleep", capture.config.GATE_SETTLE_S)])

    def test_door_opens_only_on_second_read(self):
        g2 = dict(SETTLED, ok=False, reason="door_open")
        r = self.run_at(12, gates=[GOOD_GATE, g2])
        self.assertEqual(r["skipped"], "gate_door_open")
        self.assertEqual(list(self.root.rglob("*")), [])

    def test_existing_frame_untouched(self):
        d = self.root / "frames/2026/11/24"
        d.mkdir(parents=True)
        (d / "0800.jpg").write_bytes(b"EARLIER")
        r = self.run_at(8)
        self.assertEqual(r["skipped"], "frame_exists")
        self.assertEqual(r["saved"], [])
        self.assertEqual((d / "0800.jpg").read_bytes(), b"EARLIER")
        self.assertEqual([p.name for p in d.iterdir()], ["0800.jpg"])

    def test_collision_mid_burst_removes_only_own_files(self):
        d = self.root / "frames/2026/11/24"
        d.mkdir(parents=True)
        (d / "1200-2.jpg").write_bytes(b"EARLIER")
        r = self.run_at(12)
        self.assertEqual(r["skipped"], "frame_exists")
        self.assertEqual([p.name for p in d.iterdir()], ["1200-2.jpg"])
        self.assertEqual((d / "1200-2.jpg").read_bytes(), b"EARLIER")

    def test_sidecar_failure_rolls_back_only_own(self):
        d = self.root / "frames/2026/11/24"
        d.mkdir(parents=True)
        (d / "0759.jpg").write_bytes(b"EARLIER")
        with mock.patch("timelapse.capture.storage.append_sidecar", side_effect=OSError("x")):
            r = self.run_at(8)
        self.assertEqual(r["skipped"], "write_error")
        self.assertEqual([p.name for p in d.iterdir()], ["0759.jpg"])

    def test_sidecar_time_has_offset(self):
        self.run_at(8)
        t = self.sidecar()[0]["time"]
        self.assertRegex(t, r"^2026-11-24T08:00:00[+-]\d\d:\d\d$")

    def test_camera_error(self):
        def boom():
            raise OSError("cam")
        r = self.run_at(12, fetch_snapshot=boom)
        self.assertEqual(r["skipped"], "camera_error")
        self.assertEqual(list(self.root.rglob("*")), [])

    def test_camera_error_mid_burst(self):
        n = [0]

        def flaky():
            n[0] += 1
            if n[0] == 2:
                raise OSError("cam")
            return self.jpeg
        r = self.run_at(12, fetch_snapshot=flaky)
        self.assertEqual(r["skipped"], "camera_error")
        self.assertEqual(list(self.root.rglob("*")), [])

    def test_crop_rotate_raises(self):
        with mock.patch("timelapse.capture.lossless.crop_rotate", side_effect=LosslessError("x")):
            r = self.run_at(8)
        self.assertEqual(r["skipped"], "lossless_error")
        self.assertEqual(r["saved"], [])
        self.assertEqual(list(self.root.rglob("*.jpg")), [])

    def test_crop_rotate_fails_third_frame_leaves_nothing(self):
        real = capture.lossless.crop_rotate
        n = [0]

        def f(j, c):
            n[0] += 1
            if n[0] == 3:
                raise LosslessError("x")
            return real(j, c)
        with mock.patch("timelapse.capture.lossless.crop_rotate", side_effect=f):
            r = self.run_at(12)
        self.assertEqual(r["saved"], [])
        self.assertEqual(list(self.root.rglob("*.jpg")), [])

    def test_mixed_size_burst(self):
        buf = io.BytesIO()
        Image.fromarray(np.zeros((1440, 2560, 3), "uint8")).save(buf, format="JPEG", subsampling=1)
        big = buf.getvalue()
        shots = iter([self.jpeg, big, self.jpeg])
        r = self.run_at(12, fetch_snapshot=lambda: next(shots))
        self.assertEqual(r["skipped"], "frame_mismatch")
        self.assertEqual(r["saved"], [])
        self.assertEqual(list(self.root.rglob("*")), [])

    def test_undecodable_later_shot(self):
        shots = iter([self.jpeg, b"junk", self.jpeg])
        r = self.run_at(12, fetch_snapshot=lambda: next(shots))
        self.assertEqual(r["skipped"], "frame_mismatch")
        self.assertEqual(list(self.root.rglob("*")), [])

    def test_two_runs_two_entries(self):
        self.run_at(8, 0)
        self.run_at(8, 5)
        self.assertEqual(len(self.sidecar()), 2)


if __name__ == "__main__":
    unittest.main()
