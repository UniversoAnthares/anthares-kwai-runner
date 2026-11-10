import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from tools.pinterest_today_slot_gate import has_open_slot_today, open_slots_today

TZ = ZoneInfo("America/Campo_Grande")
CID = "pinterest-test-channel"


class FakeBuffer:
    def __init__(self, slots=None, booked=None, identity=CID):
        self.slots = slots if slots is not None else ["10:49", "11:04", "12:20"]
        self.booked = booked if booked is not None else ["2026-11-10T14:49:00Z",
                                                         "2026-11-10T15:04:00Z"]
        self.identity = identity
        self.calls = []
    def __call__(self, q):
        self.calls.append(q)
        if "CortesPinterestTodayChannel" in q:
            return {"channel": {"id": self.identity, "timezone": "America/Campo_Grande",
                    "isQueuePaused": False, "postingSchedule": [
                    {"day": "tue", "paused": False, "times": self.slots}]}}
        if "CortesPinterestTodayOrganizations" in q:
            return {"account": {"organizations": [{"id": "organization-owned"}]}}
        if "CortesPinterestTodayBooked" in q:
            return {"posts": {"edges": [{"node": {"id": "post-" + str(i),
                     "channelId": CID, "dueAt": stamp, "status": "scheduled"}}
                     for i, stamp in enumerate(self.booked)],
                     "pageInfo": {"hasNextPage": False, "endCursor": None}}}
        raise AssertionError("Unexpected Buffer query")


class PinterestTodayGateTests(unittest.TestCase):
    def test_two_booked_one_free_today(self):
        api = FakeBuffer()
        now = datetime(2026, 11, 10, 9, 30, tzinfo=TZ)
        self.assertEqual(open_slots_today(api, CID, now), ["12:20"])
        self.assertTrue(has_open_slot_today(api, CID, now))

    def test_all_booked_prevents_next_day_rollover(self):
        api = FakeBuffer(booked=["2026-11-10T14:49:00Z",
                                 "2026-11-10T15:04:00Z",
                                 "2026-11-10T16:20:00Z"])
        self.assertFalse(has_open_slot_today(api, CID, datetime(2026, 11, 10, 9, 30, tzinfo=TZ)))

    def test_no_future_slot_prevents_post(self):
        api = FakeBuffer()
        self.assertFalse(has_open_slot_today(api, CID, datetime(2026, 11, 10, 13, 50, tzinfo=TZ)))
        self.assertEqual(len(api.calls), 1)

    def test_wrong_account_fails_closed(self):
        api = FakeBuffer(identity="wrong-account")
        with self.assertRaisesRegex(RuntimeError, "CHANNEL_SCHEDULE_UNVERIFIED"):
            has_open_slot_today(api, CID, datetime(2026, 11, 10, 9, 30, tzinfo=TZ))

    def test_fails_closed_when_booking_query_fails(self):
        api = FakeBuffer()
        original = api.__call__
        class Broken(FakeBuffer):
            def __call__(self, q):
                if "TodayBooked" in q:
                    return {"posts": {}}
                return super().__call__(q)
        with self.assertRaisesRegex(RuntimeError, "BOOKINGS_UNVERIFIED"):
            has_open_slot_today(Broken(), CID, datetime(2026, 11, 10, 9, 30, tzinfo=TZ))


if __name__ == "__main__":
    unittest.main()
