import unittest
from tools import pinterest_operational_evidence as p

class EvidenceContract(unittest.TestCase):
    def test_buffer_schedule_not_claimed_as_published(self):
        raw='{"pinterest_cloud":"PASS","scheduled_action":"SCHEDULED_IN_BUFFER","posts_confirmed_this_run":0}'
        state=p.inspect(raw,event="schedule",run_id="999",conclusion="success")
        self.assertEqual(state["result"],"SCHEDULED_NOT_PUBLISHED")
        self.assertEqual(state["new_public_pin_count"],0)
        self.assertTrue(state["buffer_schedule_accepted"])
        self.assertTrue(state["schedule_is_not_publication"])
        self.assertIn("não comprova publicação",p.markdown(state))
    def test_two_sent_buffer_neon_cas_uris_are_counted(self):
        raw="\n".join([
          "CORTES_PINTEREST_CONFIRMED_URL=https://www.pinterest.com/pin/819514463494255429",
          "CORTES_PINTEREST_CONFIRMED_URL=https://www.pinterest.com/pin/819514463494256008",
          '{"pinterest_cloud":"PASS","scheduled_action":"SCHEDULED_IN_BUFFER","posts_confirmed_this_run":2}'
        ])
        state=p.inspect(raw,event="workflow_dispatch",run_id="39816129186",conclusion="success")
        self.assertEqual(state["result"],"PINS_RECONCILED")
        self.assertEqual(state["new_public_pin_count"],2)
        self.assertIn("819514463494255429",p.markdown(state))
        self.assertFalse(state["independent_public_page_checked"])
    def test_mismatch_or_duplicate_never_passes(self):
        raw="\n".join([
            "CORTES_PINTEREST_CONFIRMED_URL=https://www.pinterest.com/pin/819514463494255429",
            "CORTES_PINTEREST_CONFIRMED_URL=https://www.pinterest.com/pin/819514463494255429",
            '{"pinterest_cloud":"PASS","scheduled_action":"SCHEDULED_IN_BUFFER","posts_confirmed_this_run":2}'
        ])
        state=p.inspect(raw,event="schedule",run_id="1",conclusion="success")
        self.assertEqual(state["result"],"UNVERIFIED_OR_FAILED")
        self.assertFalse(state["sent_count_matches_evidence"])
    def test_429_isolated_not_published(self):
        state=p.inspect('{"pinterest_cloud":"COOLDOWN_HTTP_429","published":0}',
            event="workflow_run",run_id="5",conclusion="success")
        self.assertEqual(state["result"],"RATE_LIMIT_ISOLATED")
        self.assertEqual(state["new_public_pin_count"],0)
    def test_board_500_recovery_without_false_publication(self):
        raw="CORTES_PINTEREST_BOARD_READ_TRANSIENT_DIRECT_BUFFER_HTTP_500\n"+\
            '{"pinterest_cloud":"PASS","scheduled_action":"SCHEDULED_IN_BUFFER","posts_confirmed_this_run":0}'
        state=p.inspect(raw,event="workflow_run",run_id="100",conclusion="success")
        self.assertTrue(state["board_500_fallback_recovered"])
        self.assertEqual(state["result"],"SCHEDULED_NOT_PUBLISHED")
    def test_no_logs_or_secrets_in_summary(self):
        raw='BUFFER_API_KEY: SECRET_veryprivate\n'+\
            '{"pinterest_cloud":"PASS","scheduled_action":"IDLE_NO_CUTS","posts_confirmed_this_run":0}'
        state=p.inspect(raw,event="schedule",run_id="100",conclusion="success")
        text=p.markdown(state)
        self.assertNotIn("SECRET_veryprivate",text)
        self.assertNotIn("BUFFER_API_KEY",text)

if __name__=="__main__":unittest.main()
