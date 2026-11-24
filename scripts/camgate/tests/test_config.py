import os
import tempfile
import unittest

from camgate.config import NO_CROP, Crop, load_crop


class LoadCropTests(unittest.TestCase):
    def conf(self, text):
        f = tempfile.NamedTemporaryFile("w", suffix=".conf", delete=False)
        f.write(text + "\n")
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_valid_crop(self):
        self.assertEqual(load_crop(self.conf("CROP=1344:1080:0:0")), Crop(1344, 1080, 0, 0))

    def test_valid_crop_among_other_keys(self):
        self.assertEqual(load_crop(self.conf("AUDIO=off\nCROP=10:20:3:4\nX=1")), Crop(10, 20, 3, 4))

    def test_missing_crop_is_none(self):
        self.assertIsNone(load_crop(self.conf("AUDIO=off")))

    def test_garbage_crop_is_none(self):
        self.assertIsNone(load_crop(self.conf("CROP=13x4:abc")))

    def test_wrong_field_count_is_none(self):
        self.assertIsNone(load_crop(self.conf("CROP=1344:1080:0")))

    def test_nonpositive_size_is_none(self):
        self.assertIsNone(load_crop(self.conf("CROP=0:1080:0:0")))

    def test_empty_crop_is_none(self):
        self.assertIsNone(load_crop(self.conf("CROP=")))

    def test_explicit_none(self):
        self.assertIs(load_crop(self.conf("CROP=none")), NO_CROP)

    def test_unreadable_file_is_none(self):
        self.assertIsNone(load_crop("/nonexistent/surveil.conf"))

    def test_commented_crop_ignored(self):
        self.assertIsNone(load_crop(self.conf("# CROP=1344:1080:0:0")))


if __name__ == "__main__":
    unittest.main()
