import json
import os
import tempfile
import unittest

from camgate import flowers
from camgate.config import NO_CROP, Crop

LIVE = Crop(1180, 1080, 164, 0)
OK = {"num": 1, "state": "opening", "x": 470, "y": 318}


class Load(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.addCleanup(self.d.cleanup)
        self.p = os.path.join(self.d.name, "public-flowers.json")

    def write(self, doc):
        with open(self.p, "w") as f:
            f.write(doc if isinstance(doc, str) else json.dumps(doc))

    def test_valid_for_live_crop(self):
        self.write({"crop": "1180:1080:164:0", "items": [OK]})
        self.assertEqual(flowers.load(self.p, LIVE), {"w": 1180, "h": 1080, "items": [OK]})

    def test_other_crop_gives_nothing(self):
        self.write({"crop": "1344:1080:0:0", "items": [OK]})
        self.assertEqual(flowers.load(self.p, LIVE)["items"], [])

    def test_no_crop_missing_or_garbage_gives_nothing(self):
        self.write({"crop": "1180:1080:164:0", "items": [OK]})
        for crop in (None, NO_CROP):
            self.assertEqual(flowers.load(self.p, crop)["items"], [])
        self.assertEqual(flowers.load(self.p + ".missing", LIVE)["items"], [])
        for bad in ("not json", "[]", '{"crop": "1180:1080:164:0", "items": "xx"}'):
            self.write(bad)
            self.assertEqual(flowers.load(self.p, LIVE)["items"], [])

    def test_bad_items_dropped(self):
        bad = [dict(OK, num=0), dict(OK, num=True), dict(OK, state="gone"), dict(OK, x=1180),
               dict(OK, y=-1), dict(OK, x=1.5), dict(OK, state="<b>"), "f1", None]
        self.write({"crop": "1180:1080:164:0", "items": bad + [OK]})
        self.assertEqual(flowers.load(self.p, LIVE)["items"], [OK])

    def test_oversized_file_gives_nothing(self):
        self.write({"crop": "1180:1080:164:0", "items": [OK], "pad": "x" * flowers.MAX_BYTES})
        self.assertEqual(flowers.load(self.p, LIVE)["items"], [])

    def test_item_cap(self):
        self.write({"crop": "1180:1080:164:0", "items": [OK] * 80})
        self.assertEqual(len(flowers.load(self.p, LIVE)["items"]), flowers.MAX_ITEMS)


if __name__ == "__main__":
    unittest.main()
