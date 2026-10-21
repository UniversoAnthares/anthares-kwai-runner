"""CORTES distribution priority, Buffer weekly windows and alternate publishers."""
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from anthares_publisher.buffer_distribution import (
    BUFFER_LIMIT_PER_SOURCE, partition_source, distribution_per_source,
    alternative_time_allowed, reserved_instants, TZ)
from tools.cortes_buffer_three_fanout import per_platform_jobs

def candidate(n):
    return {"segment_id":f"cycle:live:{n*35}:{(n+1)*35}",
            "source_id":"live","source_start":n*35,
            "source_end":(n+1)*35,"id":str(n),"dedupe_key":str(n),
            "duration_class":"short","media_url":"https://anthares.us/a.mp4"}

def calendar(now):
    return {"observed_at_utc":now.astimezone(timezone.utc).isoformat(),
            "channels":{"pinterest":{"timezone":"America/Campo_Grande",
                "queue_paused":False,
                "weekly_schedule":[{"day":"wed","paused":False,"times":["11:40","13:11"]}],
                "queued_posts":[{"due_at_utc":now.replace(hour=17,minute=0).astimezone(timezone.utc).isoformat()}]},
             "instagram":{"timezone":"America/Campo_Grande",
                "queue_paused":False,"weekly_schedule":[],"queued_posts":[]},
             "linkedin":{"timezone":"America/Campo_Grande",
                "queue_paused":False,"weekly_schedule":[],"queued_posts":[]}}}

class BufferDistributionTests(unittest.TestCase):
    def test_20_per_each_network_and_all_overflow_retained(self):
        src=[candidate(n) for n in reversed(range(70))]
        priority,overflow=partition_source(src)
        self.assertEqual((len(priority),len(overflow)),(20,50))
        self.assertEqual([x["source_start"] for x in priority],list(range(0,700,35)))
        routes=distribution_per_source("live",src)
        self.assertTrue(all(len(x)==20 for x in routes["buffer"].values()))
        self.assertTrue(all(len(x)==50 for x in routes["alternate"].values()))
        self.assertEqual(len(set(routes["buffer"]["pinterest"]) &
                             set(routes["alternate"]["pinterest"])),0)

    def test_fanout_independent_identity_for_three_accounts(self):
        records=[candidate(n) for n in range(20)]
        ids=[{x["id"] for x in per_platform_jobs(records,p)} for p in
             ("pinterest","instagram","linkedin")]
        self.assertEqual([len(x) for x in ids],[20,20,20])
        self.assertFalse(ids[0] & ids[1])
        self.assertFalse(ids[1] & ids[2])

    def test_one_clip_does_not_require_minimum(self):
        self.assertEqual(len(partition_source([candidate(0)])[0]),1)

    def test_block_overlapping_buffer_slot_even_if_queue_empty(self):
        now=datetime(2026,10,21,11,35,tzinfo=TZ)
        c=calendar(now)
        with patch("anthares_publisher.buffer_distribution.datetime") as dt:
            dt.now.return_value=now
            self.assertFalse(alternative_time_allowed(c,"pinterest",now))
            self.assertTrue(alternative_time_allowed(c,"pinterest",now.replace(hour=12,minute=10)))

    def test_block_stale_calendar_fail_closed(self):
        now=datetime.now(TZ)
        c=calendar(now-timedelta(hours=2))
        with self.assertRaisesRegex(ValueError,"STALE"):
            alternative_time_allowed(c,"pinterest",now)

    def test_booked_post_blocks_alternatives(self):
        now=datetime(2026,10,21,16,55,tzinfo=TZ)
        c=calendar(now)
        points=reserved_instants(c,"pinterest",now,now+timedelta(minutes=20))
        self.assertTrue(any(p.hour==17 and p.minute==0 for p in points))


if __name__=="__main__":
    unittest.main()
