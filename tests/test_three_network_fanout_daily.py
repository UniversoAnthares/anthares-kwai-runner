"""Offline, no-post regression for scheduled three-network fanout."""
import contextlib
import io
import json
import os
import unittest
from unittest.mock import patch

from tools import cortes_buffer_three_fanout as fanout


class ThreeNetworkDailyFanoutTests(unittest.TestCase):
    @staticmethod
    def one_master():
        return {"source_id": "source-safe-1", "segment_id": "g1:source-safe-1:10:50"}

    def test_diagnostic_does_not_enqueue(self):
        out=io.StringIO()
        with patch.object(fanout.linked,"require_cloud"), \
             patch.object(fanout.linked,"wp_state",return_value={"items":[]}), \
             patch.object(fanout.linked,"candidate_jobs",return_value=[self.one_master()]), \
             patch.object(fanout,"enqueue",side_effect=AssertionError("enqueue forbidden")), \
             patch.dict(os.environ,{"CORTES_FANOUT_DIAGNOSE_ONLY":"1"}):
            with contextlib.redirect_stdout(out):
                fanout.main()
        obj=json.loads(out.getvalue().splitlines()[-1])
        self.assertEqual(obj["new_enqueues"],0)
        self.assertEqual(obj["eligible_masters"],1)

    def test_normal_run_deduplicates_each_destination(self):
        out=io.StringIO()
        visited=[]
        def enqueue(job):
            visited.append(job["target_key"])
            return True
        with patch.object(fanout.linked,"require_cloud"), \
             patch.object(fanout.linked,"wp_state",return_value={}), \
             patch.object(fanout.linked,"candidate_jobs",return_value=[self.one_master()]), \
             patch.object(fanout,"enqueue",side_effect=enqueue), \
             patch.dict(os.environ,{"CORTES_FANOUT_DIAGNOSE_ONLY":"0"}):
            with contextlib.redirect_stdout(out):
                fanout.main()
        self.assertEqual(set(visited),set(fanout.TARGETS.values()))
        result=json.loads(out.getvalue().splitlines()[-1])
        self.assertEqual(result["distribution"]["pinterest"]["known"],1)
        self.assertTrue(result["independent_destinations"])

    def test_daily_two_hour_cycles_visit_distinct_windows(self):
        from datetime import datetime, timezone
        jobs=[{"source_id":"video-test","segment_id":f"g1:video-test:{i}:{i+40}"}
              for i in range(60)]
        seen=[]
        def enqueue(job):
            if job["target_key"]=="pinterest:lucasyahn":
                seen.append(job["segment_id"])
            return True
        def run_at(hour):
            timestamp=datetime(2026,11,10,hour,23,tzinfo=timezone.utc).timestamp()
            with patch.object(fanout.linked,"require_cloud"), \
                 patch.object(fanout.linked,"wp_state",return_value={}), \
                 patch.object(fanout.linked,"candidate_jobs",return_value=jobs), \
                 patch.object(fanout,"enqueue",side_effect=enqueue), \
                 patch.object(fanout.time,"time",return_value=timestamp), \
                 patch.dict(os.environ,{"CORTES_FANOUT_DIAGNOSE_ONLY":"0"}):
                with contextlib.redirect_stdout(io.StringIO()):
                    fanout.main()
        run_at(11)
        first=set(seen)
        seen.clear()
        run_at(13)
        second=set(seen)
        self.assertEqual(len(first | second),60)
        self.assertFalse(first & second)

    def test_five_windows_are_exhausted_without_duplicate_replay(self):
        from datetime import datetime, timezone
        jobs=[{"source_id":"five-window-test",
               "segment_id":f"g1:five-window-test:{i}:{i+40}"}
              for i in range(229)]
        seen=set()
        def enqueue(job):
            if job["target_key"]=="pinterest:lucasyahn":
                self.assertNotIn(job["segment_id"],seen)
                seen.add(job["segment_id"])
            return True
        for hour in (11,13,15,17,19):
            timestamp=datetime(2026,11,10,hour,23,tzinfo=timezone.utc).timestamp()
            with patch.object(fanout.linked,"require_cloud"), \
                 patch.object(fanout.linked,"wp_state",return_value={}), \
                 patch.object(fanout.linked,"candidate_jobs",return_value=jobs), \
                 patch.object(fanout,"enqueue",side_effect=enqueue), \
                 patch.object(fanout.time,"time",return_value=timestamp), \
                 patch.dict(os.environ,{"CORTES_FANOUT_DIAGNOSE_ONLY":"0"}):
                with contextlib.redirect_stdout(io.StringIO()):
                    fanout.main()
        self.assertEqual(len(seen),229)

    def test_preflight_failure_preserves_ledger(self):
        out=io.StringIO()
        with patch.object(fanout.linked,"require_cloud"), \
             patch.object(fanout.linked,"wp_state",side_effect=RuntimeError("CORTES_WP_STATE_MISSING")), \
             patch.object(fanout,"enqueue",side_effect=AssertionError("enqueue forbidden")):
            with contextlib.redirect_stdout(out), self.assertRaises(RuntimeError):
                fanout.main()
        self.assertIn("stage=wordpress reason=CORTES_WP_STATE_MISSING",out.getvalue())


if __name__ == "__main__":
    unittest.main()
