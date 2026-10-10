"""Static integration contract: Cloudflare queue cannot confirm a fake Kwai post."""
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class QueueBridgeTests(unittest.TestCase):
    def test_complete_requires_public_url_and_independent_id(self):
        s=(ROOT/"kwai_queue_state.sh").read_text()
        self.assertIn("KWAI_REMOTE_POST_ID must come from observed Kwai post",s)
        self.assertIn("KWAI_PUBLIC_POST_URL must be an observed public Kwai URL",s)
        self.assertIn("REMOTE_POST_ID_NOT_INDEPENDENT",s)
        self.assertIn("validate_evidence(PublicationEvidence",s)
    def test_reconcile_requires_real_public_url(self):
        s=(ROOT/"kwai_queue_state.sh").read_text()
        self.assertIn("KWAI_PUBLIC_POST_URL must be independently observed before reconciliation",s)
        self.assertIn("RECONCILIATION_REMOTE_ID_INVALID",s)
    def test_publisher_does_not_synthesize_remote_post_id(self):
        s=(ROOT/"kwai_queue_state.sh").read_text()
        self.assertNotIn('"remote_id":"kwai:"+sys.argv[1]',s)
    def test_queue_confirmation_requires_unauthenticated_public_http(self):
        s=(ROOT/"kwai_queue_state.sh").read_text()
        self.assertEqual(s.count("python3 -m anthares_publisher.public_verify"),2)
        self.assertIn("KWAI_PUBLIC_URL_NOT_INDEPENDENTLY_REACHABLE",s)
    def test_unknown_post_result_does_not_republish(self):
        s=(ROOT/"kwai_run_next_job.sh").read_text()
        self.assertIn("Never call the publisher again",s)
        self.assertIn("KWAI_JOB_REMAINS_UNCERTAIN",s)

if __name__=="__main__":unittest.main()
