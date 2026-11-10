import contextlib
import io
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from tools import cortes_buffer_pinterest_cloud as publisher


REMOTE_OLD="6ad914067d80fe56e7308119"
REMOTE_TODAY="6af3496842d372a81f6b4afd"
OID="cortes-fanout-pinterest-23108d7fbcf6db56a713e806907be474"
NID="cortes-fanout-pinterest-8ede43982585af595543fd3056584f2d"


class BufferErrorQuarantine(unittest.TestCase):
    def run_provider(self, status="error", channel=None,
                     due="2026-10-21T20:58:00Z", public=None):
        applied=[]
        def q(action,payload=None):
            if action=="pending":
                return {"jobs":[{"id":OID,"remote_id":REMOTE_OLD},
                                {"id":NID,"remote_id":REMOTE_TODAY}]}
            self.assertEqual(action,"terminal-error")
            applied.append(payload)
            return {"ok":True,"job":{"status":"failed"}}
        def api(query):
            self.assertIn("CortesPinterestErrorRecovery",query)
            return {
                "p0":{"id":REMOTE_OLD,"channelId":channel or publisher.PINTEREST_ID,
                      "status":status,"externalLink":public,
                      "schedulingType":"automatic","dueAt":due},
                "p1":{"id":REMOTE_TODAY,"channelId":publisher.PINTEREST_ID,
                      "status":"scheduled","externalLink":None,
                      "schedulingType":"automatic","dueAt":"2026-11-10T21:39:00Z"}}
        with patch.object(publisher,"queue",side_effect=q), \
             patch.object(publisher,"api",side_effect=api), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            result=publisher.reconcile_buffer_terminal_errors()
        return applied,out.getvalue(),result

    def test_exact_old_error_quarantined_never_resubmitted(self):
        jobs,output,code=self.run_provider()
        self.assertEqual(code,0)
        self.assertEqual(len(jobs),1)
        self.assertEqual(jobs[0]["remote_id"],REMOTE_OLD)
        self.assertEqual(jobs[0]["target_key"],"pinterest:lucasyahn")
        self.assertEqual(jobs[0]["provider_status"],"error")
        self.assertEqual(jobs[0]["provider_link_present"],False)
        self.assertIn('"new_posts":0',output)
        self.assertIn('"requeued_posts":0',output)
        self.assertNotIn(REMOTE_OLD,output)

    def test_scheduled_always_preserved(self):
        jobs,out,_=self.run_provider(status="scheduled")
        self.assertEqual(jobs,[])
        self.assertIn('"terminal_errors_quarantined":0',out)

    def test_wrong_buffer_account_preserved(self):
        jobs,out,_=self.run_provider(channel="different-account")
        self.assertEqual(jobs,[])
        self.assertIn('"terminal_errors_quarantined":0',out)

    def test_public_pin_present_preserved(self):
        jobs,out,_=self.run_provider(public="https://www.pinterest.com/pin/12345678")
        self.assertEqual(jobs,[])
        self.assertIn('"terminal_errors_quarantined":0',out)

    def test_recent_failure_preserved(self):
        jobs,out,_=self.run_provider(due=datetime.now(timezone.utc).isoformat())
        self.assertEqual(jobs,[])
        self.assertIn('"terminal_errors_quarantined":0',out)


if __name__=="__main__":
    unittest.main()
