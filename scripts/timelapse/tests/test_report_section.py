import json
import os
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from timelapse import report_section as rs

NOW = datetime(2026, 11, 25, 7, 0)


def mk(root, status=None, age_h=1, checkin=False):
    (root / "status").mkdir(parents=True, exist_ok=True)
    if status is not None:
        p = root / "status" / "vision-2026-11-24.json"
        p.write_text(json.dumps(status))
        t = NOW.timestamp() - age_h * 3600
        os.utime(p, (t, t))
    if checkin:
        (root / "status" / "checkin-2026-11-24.jpg").write_bytes(b"x")


class Section(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.root = Path(self.d.name)

    def tearDown(self):
        self.d.cleanup()

    def test_missing_root_is_empty(self):
        self.assertEqual(rs.timelapse_section("/nonexistent/zz", NOW),
                         {"lines": [], "checkin": None})

    def test_no_vision_run(self):
        r = rs.timelapse_section(self.root, NOW)
        self.assertEqual(r["lines"][:2], ["FLOWERS", "  no vision run yet"])
        self.assertIsNone(r["checkin"])

    def test_old_status_ignored(self):
        mk(self.root, {"status": "ok", "summary": ["x"]}, age_h=40)
        self.assertIn("  no vision run yet", rs.timelapse_section(self.root, NOW)["lines"])

    def test_ok_summary_and_checkin(self):
        mk(self.root, {"status": "ok", "summary": ["f1 opened"], "pending": ["f2"]},
           checkin=True)
        r = rs.timelapse_section(self.root, NOW)
        self.assertIn("  f1 opened", r["lines"])
        self.assertIn("  " + rs.NEEDS_YOU, r["lines"])
        self.assertTrue(r["checkin"].endswith("checkin-2026-11-24.jpg"))

    def test_pending_without_image(self):
        mk(self.root, {"status": "ok", "summary": [], "pending": ["f2"]})
        r = rs.timelapse_section(self.root, NOW)
        self.assertIsNone(r["checkin"])
        self.assertNotIn("  " + rs.NEEDS_YOU, r["lines"])

    def test_failed_status(self):
        mk(self.root, {"status": "vision_failed", "why": "boom"})
        self.assertIn("  vision vision_failed: boom", rs.timelapse_section(self.root, NOW)["lines"])

    def test_archive_line(self):
        y = self.root / "frames/2026/11/24"
        y.mkdir(parents=True)
        (y / "day.json").write_text(json.dumps({"frames": [{}, {}, {}]}))
        (y / "a.jpg").write_bytes(b"0" * 1000)
        (self.root / "logs").mkdir()
        (self.root / "logs" / "capture.log").write_text(
            "2026-11-24T10:00:00 saved=3 skipped=None\n"
            "2026-11-24T10:10:00 saved=0 skipped=mist_recent\n"
            "2026-11-24T10:20:00 saved=0 skipped=mist_recent\n"
            "2026-11-23T10:20:00 saved=0 skipped=after_private\n")
        line = [l for l in rs.timelapse_section(self.root, NOW)["lines"] if "archive:" in l][0]
        self.assertIn("3 frames yesterday", line)
        self.assertIn("{mist_recent: 2}", line)

    def test_garbage_never_raises(self):
        mk(self.root)
        (self.root / "status" / "vision-2026-11-24.json").write_text("{not json")
        self.assertEqual(rs.timelapse_section(self.root, NOW),
                         {"lines": [], "checkin": None})


if __name__ == "__main__":
    unittest.main()
