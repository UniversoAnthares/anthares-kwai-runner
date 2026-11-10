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
