import threading
import unittest

from camgate.__main__ import tick_loop
from camgate.archive_gate import ArchiveGate
from camgate.policy import Decision


class ArchiveGateTest(unittest.TestCase):
    def test_starts_not_ok_and_last_not_ok_is_start(self):
        g = ArchiveGate(clock=lambda: 100.0)
        s = g.state(100.0)
        self.assertFalse(s["ok"])
        self.assertEqual(s["last_not_ok_at"], 100.0)

    def test_ok_after_ok_observation_keeps_last_not_ok(self):
        g = ArchiveGate(clock=lambda: 100.0)
        g.observe(102.0, Decision(True, "ok"))
        s = g.state(102.5)
        self.assertTrue(s["ok"])
        self.assertEqual(s["last_not_ok_at"], 100.0)
        self.assertEqual(s["now"], 102.5)

    def test_showme_is_not_ok(self):
        g = ArchiveGate(clock=lambda: 0.0)
        g.observe(10.0, Decision(True, "showme"))
        s = g.state(10.0)
        self.assertFalse(s["ok"])
        self.assertEqual(s["last_not_ok_at"], 10.0)
        self.assertEqual(s["reason"], "showme")

    def test_stale_observation_is_not_ok(self):
        g = ArchiveGate(clock=lambda: 0.0)
        g.observe(10.0, Decision(True, "ok"))
        self.assertFalse(g.state(13.5)["ok"])

    def test_doors_open_resets_last_not_ok(self):
        g = ArchiveGate(clock=lambda: 0.0)
        g.observe(10.0, Decision(True, "ok"))
        g.observe(20.0, Decision(False, "doors_open"))
        g.observe(21.0, Decision(True, "ok"))
        self.assertEqual(g.state(21.0)["last_not_ok_at"], 20.0)

    def test_gap_in_observation_counts_as_not_ok(self):
        g = ArchiveGate(clock=lambda: 0.0)
        g.observe(1.0, Decision(True, "ok"))
        g.observe(10.0, Decision(True, "ok"))
        g.observe(100.0, Decision(True, "ok"))
        s = g.state(100.0)
        self.assertTrue(s["ok"])
        self.assertEqual(s["last_not_ok_at"], 100.0)

    def test_first_observation_long_after_start_is_a_gap(self):
        g = ArchiveGate(clock=lambda: 100.0)
        g.observe(105.0, Decision(True, "ok"))
        self.assertEqual(g.state(105.0)["last_not_ok_at"], 105.0)

    def test_continuous_observation_keeps_last_not_ok(self):
        g = ArchiveGate(clock=lambda: 0.0)
        for t in (1.0, 2.0, 3.0, 4.0, 5.0):
            g.observe(t, Decision(True, "ok"))
        self.assertEqual(g.state(5.0)["last_not_ok_at"], 0.0)

    def test_tick_loop_feeds_gate(self):
        stop = threading.Event()
        g = ArchiveGate(clock=lambda: 0.0)

        class K:
            def tick(self):
                stop.set()

        tick_loop(K(), interval=0.01, stop=stop, gate=g, decide_fn=lambda now: Decision(True, "ok"), clock=lambda: 5.0)
        self.assertTrue(g.state(5.0)["ok"])


if __name__ == "__main__":
    unittest.main()
