import unittest
from types import SimpleNamespace

from camgate.config import TOPIC_DOORS, TOPIC_SHOWME
from camgate.policy import DoorSignal, ShowMe
from camgate.signals import SignalStore, parse_doors, parse_showme

GOOD = b'{"open":false,"left":0,"right":0,"serial_age_s":4,"ts":999.5}'


class FakeClient:
    def subscribe(self, topics):
        pass


def msg(topic, payload):
    return SimpleNamespace(topic=topic, payload=payload)


class ParseDoorsTests(unittest.TestCase):
    def test_closed(self):
        self.assertEqual(parse_doors(GOOD), DoorSignal(False, 4, 999.5))

    def test_unknown(self):
        p = b'{"open":null,"left":null,"right":0,"serial_age_s":4,"ts":999.5}'
        self.assertIsNone(parse_doors(p).open)

    def test_malformed(self):
        self.assertIsNone(parse_doors(b"not json"))
        self.assertIsNone(parse_doors(b'{"open":"no"}'))
        self.assertIsNone(parse_doors(b"\xff\xfe"))
        self.assertIsNone(parse_doors(b"[1,2]"))
        self.assertIsNone(parse_doors(b"null"))

    def test_strict_types(self):
        bad = [
            b'{"open":"no","serial_age_s":4,"ts":1}',
            b'{"open":0,"serial_age_s":4,"ts":1}',
            b'{"open":false,"serial_age_s":true,"ts":1}',
            b'{"open":false,"serial_age_s":4,"ts":true}',
            b'{"open":false,"serial_age_s":"4","ts":1}',
            b'{"open":false,"serial_age_s":NaN,"ts":1}',
            b'{"open":false,"serial_age_s":4,"ts":Infinity}',
            b'{"open":false,"ts":1}',
            b'{"open":false,"serial_age_s":4}',
            b'{"serial_age_s":4,"ts":1}',
        ]
        for p in bad:
            self.assertIsNone(parse_doors(p), p)


class ParseShowMeTests(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(parse_showme(b'{"on":true,"until":1600,"ts":1000}'), ShowMe(True, 1600))

    def test_off_null_until(self):
        self.assertEqual(parse_showme(b'{"on":false,"until":null,"ts":1000}'), ShowMe(False, None))

    def test_malformed(self):
        for p in [b"x", b'{"on":1,"until":5,"ts":1}', b'{"on":true,"until":"5","ts":1}',
                  b'{"on":true,"until":true,"ts":1}', b'{"on":true,"until":NaN,"ts":1}',
                  b'{"until":5,"ts":1}', b'{"on":true,"until":5}', b"[]"]:
            self.assertIsNone(parse_showme(p), p)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.store = SignalStore()
        self.sig = DoorSignal(False, 4, 999.5)

    def test_starts_private(self):
        self.store.set_doors(self.sig)
        self.store.set_showme(ShowMe(True, 5))
        self.assertEqual(self.store.snapshot(), (None, None))

    def test_connected_returns_both(self):
        self.store.set_connected(True)
        self.store.set_doors(self.sig)
        self.store.set_showme(ShowMe(True, 5))
        self.assertEqual(self.store.snapshot(), (self.sig, ShowMe(True, 5)))

    def test_disconnected_hides_doors_and_showme(self):
        self.store.set_connected(True)
        self.store.set_doors(self.sig)
        self.store.set_showme(ShowMe(True, 5))
        self.store.set_connected(False)
        self.assertEqual(self.store.snapshot(), (None, None))

    def test_on_message_routes(self):
        self.store.on_connect(FakeClient(), None, None, 0, None)
        self.store.on_message(None, None, msg(TOPIC_DOORS, GOOD))
        self.store.on_message(None, None, msg(TOPIC_SHOWME, b'{"on":true,"until":1600,"ts":1}'))
        self.assertEqual(self.store.snapshot(), (self.sig, ShowMe(True, 1600)))

    def test_malformed_doors_clears_doors(self):
        self.store.on_connect(FakeClient(), None, None, 0, None)
        self.store.on_message(None, None, msg(TOPIC_DOORS, GOOD))
        self.store.on_message(None, None, msg(TOPIC_DOORS, b"garbage"))
        self.assertIsNone(self.store.snapshot()[0])

    def test_malformed_showme_clears_showme(self):
        self.store.on_connect(FakeClient(), None, None, 0, None)
        self.store.on_message(None, None, msg(TOPIC_SHOWME, b'{"on":true,"until":1600,"ts":1}'))
        self.store.on_message(None, None, msg(TOPIC_SHOWME, b"garbage"))
        self.assertIsNone(self.store.snapshot()[1])

    def test_unknown_topic_ignored(self):
        self.store.on_connect(FakeClient(), None, None, 0, None)
        self.store.on_message(None, None, msg(TOPIC_DOORS, GOOD))
        self.store.on_message(None, None, msg("other/topic", b"x"))
        self.assertEqual(self.store.snapshot()[0], self.sig)

    def test_on_disconnect_hides(self):
        self.store.on_connect(FakeClient(), None, None, 0, None)
        self.store.on_message(None, None, msg(TOPIC_DOORS, GOOD))
        self.store.on_disconnect(None, None, None, 0, None)
        self.assertEqual(self.store.snapshot(), (None, None))

    def test_failed_connect_stays_private(self):
        # reason code 5 = not authorised; int or paho ReasonCode both must not connect
        self.store.on_connect(FakeClient(), None, None, 5, None)
        self.store.on_message(None, None, msg(TOPIC_DOORS, GOOD))
        self.assertEqual(self.store.snapshot(), (None, None))

    def test_on_connect_subscribes_qos1(self):
        calls = []
        client = SimpleNamespace(subscribe=lambda topics: calls.append(topics))
        self.store.on_connect(client, None, None, 0, None)
        self.assertEqual(calls, [[(TOPIC_DOORS, 1), (TOPIC_SHOWME, 1)]])

    def test_on_message_never_raises(self):
        self.store.on_message(None, None, SimpleNamespace(topic=None, payload=None))


if __name__ == "__main__":
    unittest.main()
