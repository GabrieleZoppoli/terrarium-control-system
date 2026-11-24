import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from timelapse import vision


def _img(p, w=1168, h=1080):
    Image.new("RGB", (w, h), (30, 80, 30)).save(p, "JPEG")


def _day(root, frames):
    d = Path(root) / "frames" / "2026" / "11" / "24"
    d.mkdir(parents=True)
    entries = []
    for t, phase, names, sharp in frames:
        for n in names:
            if n:
                _img(d / n)
        entries.append({"time": t, "files": ["frames/2026/11/24/" + n for n in names],
                        "phase": phase, "geometry": "g", "sharpness": sharp})
    (d / "day.json").write_text(json.dumps({"frames": entries}))
    return d


class TestPickBest(unittest.TestCase):
    def test_prefers_plateau(self):
        with tempfile.TemporaryDirectory() as t:
            d = _day(t, [("a", "lit", ["1000.jpg"], [99.0]),
                         ("b", "plateau", ["1200.jpg", "1200-1.jpg"], [5.0, 7.0]),
                         ("c", "night", ["0300.jpg"], [500.0])])
            self.assertEqual(vision.pick_best(d), d / "1200-1.jpg")

    def test_lit_fallback_never_night(self):
        with tempfile.TemporaryDirectory() as t:
            d = _day(t, [("a", "lit", ["1000.jpg"], [3.0]), ("c", "night", ["0300.jpg"], [500.0])])
            self.assertEqual(vision.pick_best(d), d / "1000.jpg")
        with tempfile.TemporaryDirectory() as t:
            d = _day(t, [("c", "night", ["0300.jpg"], [500.0])])
            self.assertIsNone(vision.pick_best(d))

    def test_empty_or_corrupt(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertIsNone(vision.pick_best(Path(t)))
            (Path(t) / "day.json").write_text("{nope")
            self.assertIsNone(vision.pick_best(Path(t)))


REG = {"items": {
    "1": {"id": "1", "state": "open", "stalk": "A", "x": 5, "y": 500},
    "2": {"id": "2", "state": "bud", "stalk": "B", "x": 600, "y": 540, "needs_owner": True},
    "3": {"id": "3", "state": "gone", "stalk": "C", "x": 300, "y": 300}}}


class TestInputs(unittest.TestCase):
    def test_build(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            a, b = t / "a.jpg", t / "b.jpg"
            _img(a), _img(b)
            w = t / "w"
            w.mkdir()
            out = vision.build_inputs(a, b, REG, w)
            self.assertEqual([p.name for p in out], ["overview.jpg", "item-1.jpg", "item-2.jpg"])
            self.assertEqual(Image.open(w / "item-1.jpg").size, (1600, 800))
            self.assertEqual(Image.open(w / "overview.jpg").size, (584, 540))
            out = vision.build_inputs(a, None, REG, w)
            self.assertEqual(len(out), 3)

    def test_prompt(self):
        s = vision.build_prompt(REG, ["overview.jpg", "item-1.jpg", "item-2.jpg"])
        for k in ("overview.jpg", "item-1.jpg", "item-2.jpg", "shape", "confidence", "JSON"):
            self.assertIn(k, s)
        self.assertNotIn("item-3.jpg", s)


if __name__ == "__main__":
    unittest.main()
