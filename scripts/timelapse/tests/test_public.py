import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from camgate.config import NO_CROP, Crop
from timelapse import config, public, registry

GEO = "1168x1080+176+0/rot180"
LIVE = Crop(1180, 1080, 164, 0)


def item(state="opening", x=470, y=318, confirmed=True, needs_owner=False, streak=0):
    return {"state": state, "x": x, "y": y, "confirmed": confirmed,
            "needs_owner": needs_owner, "streak": streak}


def reg(**items):
    return {"geometry": GEO, "items": items, "runs": []}


class Geometry(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(public.parse_geometry(GEO), Crop(1168, 1080, 176, 0))
        for bad in ("", "1168x1080+176+0", "axb+1+2/rot180", None):
            self.assertIsNone(public.parse_geometry(bad))

    def test_live_crop_maps_archive_to_same_pixel(self):
        self.assertEqual(public.to_public_xy(470, 318, Crop(1168, 1080, 176, 0), LIVE), (470, 318))

    def test_other_crop_shifts(self):
        # raw x = 176 + 1167 - 470 = 873; public x = 1299 - 873 = 426
        self.assertEqual(public.to_public_xy(470, 318, Crop(1168, 1080, 176, 0),
                                             Crop(1300, 1080, 0, 0)), (426, 318))


class Build(unittest.TestCase):
    def test_only_trusted_visible_items(self):
        doc = public.build(reg(
            f1=item(),
            f2=item(needs_owner=True),
            f3=item(confirmed=False, streak=2),
            f4=item(confirmed=False, streak=3, state="open", x=995, y=645),
            f5=item(state="gone"),
            f6=item(state="hidden"),
        ), LIVE)
        self.assertEqual(doc["crop"], "1180:1080:164:0")
        self.assertEqual((doc["w"], doc["h"]), (1180, 1080))
        self.assertEqual(doc["items"], [
            {"num": 1, "state": "opening", "x": 470, "y": 318},
            {"num": 4, "state": "open", "x": 995, "y": 645},
        ])

    def test_out_of_public_frame_dropped(self):
        doc = public.build(reg(f1=item(x=0)), Crop(1100, 1080, 164, 0))
        self.assertEqual(doc["items"], [])

    def test_odd_ids_dropped(self):
        doc = public.build(reg(x1=item(), f=item()), LIVE)
        self.assertEqual(doc["items"], [])

    def test_no_crop_or_bad_geometry_is_empty(self):
        for r, c in ((reg(f1=item()), NO_CROP), (reg(f1=item()), None),
                     ({"geometry": "", "items": {"f1": item()}}, LIVE)):
            doc = public.build(r, c)
            self.assertEqual((doc["crop"], doc["items"]), ("", []))


class SaveWritesPublic(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.addCleanup(self.d.cleanup)
        self.conf = os.path.join(self.d.name, "surveil.conf")
        Path(self.conf).write_text("CROP=1180:1080:164:0\n")
        self.regp = os.path.join(self.d.name, "registry.json")
        self.pub = Path(self.d.name) / "public-flowers.json"

    def save(self, r):
        with mock.patch.object(config, "SURVEIL_CONF", self.conf), \
                contextlib.redirect_stderr(io.StringIO()) as err:
            registry.save(self.regp, r)
        return err.getvalue()

    def test_save_refreshes_public_file(self):
        self.save(reg(f1=item()))
        doc = json.loads(self.pub.read_text())
        self.assertEqual(doc["items"], [{"num": 1, "state": "opening", "x": 470, "y": 318}])
        self.save(reg(f1=item(needs_owner=True)))
        self.assertEqual(json.loads(self.pub.read_text())["items"], [])

    def test_broken_item_removes_stale_public_file_but_saves_registry(self):
        self.save(reg(f1=item()))
        self.assertTrue(self.pub.exists())
        broken = reg(f1={"state": "open", "confirmed": True})  # no x/y
        err = self.save(broken)
        self.assertFalse(self.pub.exists())
        self.assertIn("public flower list not written", err)
        self.assertEqual(registry.load(self.regp), broken)


if __name__ == "__main__":
    unittest.main()
