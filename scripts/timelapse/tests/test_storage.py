import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from timelapse import storage


class StorageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_frame_path(self):
        t = datetime(2026, 11, 24, 9, 5)
        self.assertEqual(storage.frame_path(self.root, t, None),
                         self.root / "frames/2026/11/24/0905.jpg")
        self.assertEqual(storage.frame_path(self.root, t, 2),
                         self.root / "frames/2026/11/24/0905-2.jpg")

    def test_write_atomic(self):
        p = self.root / "a" / "b.jpg"
        storage.write_atomic(p, b"xyz")
        self.assertEqual(p.read_bytes(), b"xyz")
        self.assertEqual([x.name for x in p.parent.iterdir()], ["b.jpg"])

    def test_sidecar_appends(self):
        d = self.root / "day"
        storage.append_sidecar(d, {"a": 1})
        storage.append_sidecar(d, {"a": 2})
        self.assertEqual(json.loads((d / "day.json").read_text()),
                         {"frames": [{"a": 1}, {"a": 2}]})

    def test_sidecar_corrupt_is_replaced_not_crash(self):
        d = self.root / "day"
        d.mkdir()
        (d / "day.json").write_text("{bad")
        storage.append_sidecar(d, {"a": 1})
        self.assertEqual(json.loads((d / "day.json").read_text())["frames"], [{"a": 1}])

    def test_space_ok_full_low(self):
        (self.root / "f.bin").write_bytes(b"0" * 2048)
        gb = 1024 ** 3
        with mock.patch("shutil.disk_usage", return_value=shutil._ntuple_diskusage(100 * gb, 0, 50 * gb)):
            self.assertIsNone(storage.space_check(self.root, 40, 15))
            self.assertEqual(storage.space_check(self.root, 0.000001, 15), "archive_full")
        with mock.patch("shutil.disk_usage", return_value=shutil._ntuple_diskusage(100 * gb, 0, 10 * gb)):
            self.assertEqual(storage.space_check(self.root, 40, 15), "disk_low")


if __name__ == "__main__":
    unittest.main()
