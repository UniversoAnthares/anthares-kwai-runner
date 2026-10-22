"""Buffer explicit MutationError vs uncertain transport, P0 and CAS."""
import unittest
from pathlib import Path
from social_adapters.buffer_three_channels import redacted_mutation_diagnostic, BufferDefiniteRejection

ROOT=Path(__file__).resolve().parents[1]
class BufferExplicitRejection(unittest.TestCase):
    def test_redaction_removes_links_emails_identifiers(self):
        s=redacted_mutation_diagnostic('Invalid Pinterest title "secret private content" from https://anthares.us/a.mp4 user@anthares.us token abcdefghijklmnopqrstuvwxyz012345')
        self.assertNotIn('secret private content',s)
        self.assertNotIn('https:',s)
        self.assertNotIn('user@',s)
        self.assertNotIn('abcdefghijklmnopqrstuvwxyz012345',s)
        self.assertIn('Invalid Pinterest title',s)
    def test_typed_rejection_proves_no_remote_post(self):
        cls=BufferDefiniteRejection('METADATA','Invalid title')
        self.assertEqual(cls.classification,'METADATA')
        self.assertIn('BUFFER_MUTATION_REJECTED_METADATA',str(cls))
        backend=(ROOT/'infra/neon-cortes-queue/index.mjs').read_text(encoding='utf8')
        self.assertIn("status='started' AND remote_id IS NULL",backend)
        self.assertIn('BUFFER_REJECTED_FENCE_REJECTED',backend)
        self.assertIn("'buffer_typed_rejection'",backend)
        self.assertIn("interval '120 minutes'",backend)
    def test_never_conflate_transport_with_typed_rejection(self):
        code=(ROOT/'tools/cortes_buffer_pinterest_cloud.py').read_text(encoding='utf8')
        self.assertIn('except BufferDefiniteRejection as exc:',code)
        self.assertIn('queue("rejected",{**fence,"reason":exc.classification})',code)
        self.assertIn('notify_buffer_rejection_p0',code)
        self.assertIn('except Exception:',code)
        queue=(ROOT/'tools/cortes_queue_ha.py').read_text(encoding='utf8')
        self.assertIn('"buffer-rejected"',queue)
if __name__=='__main__':unittest.main()
