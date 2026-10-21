"""One social destination fails; other networks continue without sharing state."""
import unittest
from unittest.mock import patch
from tools import cortes_buffer_three_fanout as fanout


def masters(count):
    return [{"source_id":"live01","segment_id":f"live01:{i*1000}:{i*1000+55000}",
             "media_url":"https://anthares.us/sample.mp4","source_start":i*1000,
             "source_end":i*1000+55000,"duration_seconds":55,"title":"Universo Anthares",
             "duration_class":"short","media_sha256":"a"*64,"account_id":"primary"} for i in range(count)]


class IndependentDestinations(unittest.TestCase):
    def test_one_network_failure_does_not_block_others(self):
        visited=[]
        def send(job):
            visited.append(job["platform"])
            if job["platform"]=="pinterest":
                raise RuntimeError("PIN_LIMIT")
            return False
        with patch.object(fanout.linked,"require_cloud"),patch.object(fanout.linked,"wp_state",return_value={}):
            with patch.object(fanout.linked,"candidate_jobs",return_value=masters(1)):
                with patch.object(fanout,"enqueue",side_effect=send):
                    with self.assertRaisesRegex(RuntimeError,"pinterest"):
                        fanout.main()
        self.assertIn("instagram",visited)
        self.assertIn("pinterest",visited)
        self.assertIn("linkedin",visited)

    def test_100_short_masters_generate_300_independent_destinations(self):
        visited=[]
        with patch.object(fanout.linked,"require_cloud"),patch.object(fanout.linked,"wp_state",return_value={}):
            with patch.object(fanout.linked,"candidate_jobs",return_value=masters(100)):
                with patch.object(fanout,"enqueue",side_effect=lambda j:visited.append(j) or False):
                    fanout.main()
        self.assertEqual({x["platform"] for x in visited},{"instagram","pinterest","linkedin"})
        self.assertEqual(len(visited),150) # 50 per-network per run, remainder handled next run
        self.assertEqual(len({x["id"] for x in visited}),150)
        for platform in ("instagram","pinterest","linkedin"):
            self.assertEqual(sum(x["platform"]==platform for x in visited),50)


if __name__=="__main__":
    unittest.main()
