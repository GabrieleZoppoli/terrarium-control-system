import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

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


    def test_ignores_invalid(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "frames" / "2026" / "11" / "24"
            d.mkdir(parents=True)
            for n in ("1000.jpg", "1100.jpg", ".hid.jpg", "1300.jpg"):
                _img(d / n)
            fr = [
                {"phase": "plateau", "files": ["x/ghost.jpg"], "sharpness": [999.0]},
                {"phase": "plateau", "files": ["x/.hid.jpg"], "sharpness": [998.0]},
                {"phase": "plateau", "files": ["x/1100.jpg", "x/1300.jpg"], "sharpness": [997.0]},
                {"phase": "plateau", "files": ["x/1300.jpg"], "sharpness": ["abc"]},
                {"phase": "plateau", "files": "oops", "sharpness": None},
                {"phase": "plateau"},
                "junk",
                {"phase": "plateau", "files": ["x/1000.jpg"], "sharpness": [2.0]},
            ]
            (d / "day.json").write_text(json.dumps({"frames": fr}))
            self.assertEqual(vision.pick_best(d), d / "1000.jpg")
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d / "day.json").write_text(json.dumps({"frames": [
                {"phase": "plateau", "files": ["ghost.jpg"], "sharpness": [1.0]}, "junk"]}))
            self.assertIsNone(vision.pick_best(d))


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

    def _pair(self, t):
        today = Image.new("RGB", (1168, 1080), (0, 0, 255))
        yest = Image.new("RGB", (1168, 1080), (255, 0, 0))
        ImageDraw.Draw(today).rectangle([0, 0, 40, 40], fill=(0, 255, 0))
        ImageDraw.Draw(today).rectangle([580, 520, 620, 560], fill=(0, 255, 0))
        a, b = Path(t) / "a.jpg", Path(t) / "b.jpg"
        today.save(a, "JPEG", quality=95)
        yest.save(b, "JPEG", quality=95)
        return a, b

    @staticmethod
    def _near(px, want, tol=40):
        return all(abs(p - w) <= tol for p, w in zip(px, want))

    def test_crop_geometry(self):
        reg = {"items": {
            "1": {"id": "1", "state": "open", "stalk": "A", "x": 5, "y": 5},
            "2": {"id": "2", "state": "bud", "stalk": "B", "x": 600, "y": 540},
            "3": {"id": "3", "state": "gone", "stalk": "C", "x": 300, "y": 300}}}
        with tempfile.TemporaryDirectory() as t:
            a, b = self._pair(t)
            w = Path(t) / "w"
            vision.build_inputs(a, b, reg, w)
            self.assertFalse((w / "item-3.jpg").exists())
            g, bl, r = (0, 255, 0), (0, 0, 255), (255, 0, 0)
            im = Image.open(w / "item-2.jpg").convert("RGB")
            self.assertEqual(im.size, (1600, 800))
            self.assertTrue(self._near(im.getpixel((400, 400)), g))
            self.assertTrue(self._near(im.getpixel((100, 100)), bl))
            self.assertTrue(self._near(im.getpixel((1200, 400)), r))
            self.assertTrue(self._near(im.getpixel((900, 100)), r))
            e = Image.open(w / "item-1.jpg").convert("RGB")
            self.assertEqual(e.size, (1600, 800))
            self.assertTrue(self._near(e.getpixel((20, 20)), g))
            self.assertTrue(self._near(e.getpixel((700, 700)), bl))
            self.assertTrue(self._near(e.getpixel((1000, 700)), r))
            self.assertTrue(self._near(e.getpixel((1590, 790)), r))

    def test_overview_dot_position(self):
        reg = {"items": {"1": {"id": "1", "state": "open", "stalk": "A", "x": 400, "y": 300}}}
        with tempfile.TemporaryDirectory() as t:
            a, b = self._pair(t)
            vision.build_inputs(a, b, reg, Path(t) / "w")
            ov = Image.open(Path(t) / "w" / "overview.jpg").convert("RGB")
            self.assertTrue(min(ov.getpixel((200, 150))) > 220)
            self.assertFalse(min(ov.getpixel((200, 170))) > 220)

    def test_prompt_content(self):
        s = vision.build_prompt(REG, ["overview.jpg", "item-1.jpg", "item-2.jpg"])
        for k in ("pink", "joint", "0 and 1", "bud", "opening", "open", "fading", "gone",
                  "hidden", "id 1", "id 2"):
            self.assertIn(k, s)
        self.assertNotIn("id 3", s)

    def test_prompt(self):
        s = vision.build_prompt(REG, ["overview.jpg", "item-1.jpg", "item-2.jpg"])
        for k in ("overview.jpg", "item-1.jpg", "item-2.jpg", "shape", "confidence", "JSON"):
            self.assertIn(k, s)
        self.assertNotIn("item-3.jpg", s)


if __name__ == "__main__":
    unittest.main()
