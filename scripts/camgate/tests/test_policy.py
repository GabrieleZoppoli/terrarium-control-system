import unittest

from camgate.config import NO_CROP, Crop
from camgate.policy import Decision, DoorSignal, ShowMe, decide

CROP = Crop(1344, 1080, 0, 0)
NOW = 1000.0


class DecideTests(unittest.TestCase):
    def test_closed_fresh_is_public(self):
        self.assertEqual(decide(NOW, DoorSignal(False, 5, 999.5), None, CROP), Decision(True, "ok"))

    def test_no_crop_sentinel_is_valid(self):
        self.assertEqual(decide(NOW, DoorSignal(False, 5, 999.5), None, NO_CROP), Decision(True, "ok"))

    def test_open_is_private(self):
        self.assertEqual(decide(NOW, DoorSignal(True, 5, 999.5), None, CROP), Decision(False, "doors_open"))

    def test_no_signal_yet_is_private(self):
        self.assertEqual(decide(NOW, None, None, CROP), Decision(False, "door_state_unknown"))

    def test_unknown_door_is_private(self):
        self.assertEqual(decide(NOW, DoorSignal(None, 5, 999.5), None, CROP), Decision(False, "door_state_unknown"))

    def test_stale_signal_is_private(self):
        self.assertEqual(decide(NOW, DoorSignal(False, 5, 996.9), None, CROP), Decision(False, "door_signal_stale"))

    def test_stale_boundary_is_strict(self):
        self.assertEqual(decide(NOW, DoorSignal(False, 5, 997.0), None, CROP), Decision(True, "ok"))

    def test_serial_stale_is_private(self):
        self.assertEqual(decide(NOW, DoorSignal(False, 91, 999.5), None, CROP), Decision(False, "serial_stale"))

    def test_serial_boundary_is_strict(self):
        self.assertEqual(decide(NOW, DoorSignal(False, 90, 999.5), None, CROP), Decision(True, "ok"))

    def test_nan_values_fail_closed(self):
        nan = float("nan")
        self.assertFalse(decide(NOW, DoorSignal(False, nan, 999.5), None, CROP).public)
        self.assertFalse(decide(NOW, DoorSignal(False, 5, nan), None, CROP).public)
        self.assertFalse(decide(NOW, DoorSignal(True, 5, 999.5), ShowMe(True, nan), CROP).public)

    def test_showme_overrides_open_door(self):
        self.assertEqual(decide(NOW, DoorSignal(True, 5, 999.5), ShowMe(True, 1600), CROP), Decision(True, "showme"))

    def test_showme_overrides_stale_signal(self):
        self.assertEqual(decide(NOW, None, ShowMe(True, 1600), CROP), Decision(True, "showme"))

    def test_showme_off_is_ignored(self):
        self.assertEqual(decide(NOW, DoorSignal(True, 5, 999.5), ShowMe(False, 1600), CROP), Decision(False, "doors_open"))

    def test_showme_without_expiry_is_ignored(self):
        self.assertEqual(decide(NOW, DoorSignal(True, 5, 999.5), ShowMe(True, None), CROP), Decision(False, "doors_open"))

    def test_expired_showme_is_ignored(self):
        self.assertEqual(decide(NOW, DoorSignal(True, 5, 999.5), ShowMe(True, 999), CROP), Decision(False, "doors_open"))

    def test_showme_expiring_exactly_now_is_ignored(self):
        self.assertEqual(decide(NOW, DoorSignal(True, 5, 999.5), ShowMe(True, 1000.0), CROP), Decision(False, "doors_open"))

    def test_showme_too_long_is_ignored(self):
        self.assertEqual(decide(NOW, DoorSignal(True, 5, 999.5), ShowMe(True, NOW + 1801), CROP), Decision(False, "doors_open"))

    def test_showme_max_boundary_is_allowed(self):
        self.assertEqual(decide(NOW, DoorSignal(True, 5, 999.5), ShowMe(True, NOW + 1800), CROP), Decision(True, "showme"))

    def test_invalid_crop_beats_everything(self):
        self.assertEqual(decide(NOW, DoorSignal(False, 5, 999.5), ShowMe(True, 1600), None), Decision(False, "crop_invalid"))


if __name__ == "__main__":
    unittest.main()
