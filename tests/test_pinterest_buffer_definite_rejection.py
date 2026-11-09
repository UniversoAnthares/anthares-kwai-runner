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

    def test_instagram_media_rejection_is_terminal_without_retry(self):
        from unittest.mock import patch
        from tools import cortes_buffer_instagram_cloud as ig
        actions=[]
        job={"id":"cortes-fanout-instagram-example","lease_generation":7}
        payload={"platform":"instagram","account_id":"universoanthares",
                 "media_url":"https://anthares.us/short.mp4","duration_seconds":40,
                 "title":"short title"}
        def fake_queue(verb,data=None):
            actions.append(verb)
            if verb=="lease":return {"job":job}
            if verb=="rejected":
                self.assertEqual(data["reason"],"MEDIA")
                self.assertEqual(data["lease_generation"],7)
                return {"ok":True,"job":{"status":"failed"}}
            if verb=="start":return {"ok":True}
            raise AssertionError("Unexpected write: "+verb)
        with patch.object(ig,"queue",side_effect=fake_queue),\
             patch.object(ig,"safe_payload",return_value=payload),\
             patch("social_adapters.buffer_three_channels.prepare",return_value={}),\
             patch.object(ig,"source_media_is_404",return_value=False),\
             patch.object(ig,"schedule",side_effect=BufferDefiniteRejection("MEDIA","Media rejected")):
            self.assertEqual(ig.publish_once(),"DEFINITE_REJECTION_MEDIA_FENCED")
        self.assertEqual(actions,["lease","start","rejected"])
        backend=(ROOT/"infra/neon-cortes-queue/index.mjs").read_text(encoding="utf8")
        self.assertIn("terminalMedia=platform==='instagram'&&reason==='MEDIA'",backend)
        self.assertIn("WHEN $6::boolean THEN 'failed' ELSE 'queued'",backend)

    def test_instagram_transport_uncertain_preserves_existing_fail_fence(self):
        from unittest.mock import patch
        from tools import cortes_buffer_instagram_cloud as ig
        actions=[]
        job={"id":"cortes-fanout-instagram-example","lease_generation":7}
        payload={"platform":"instagram","account_id":"universoanthares",
                 "media_url":"https://anthares.us/short.mp4","duration_seconds":40,
                 "title":"short title"}
        def fake_queue(verb,data=None):
            actions.append(verb)
            if verb=="lease":return {"job":job}
            return {"ok":True}
        with patch.object(ig,"queue",side_effect=fake_queue),\
             patch.object(ig,"safe_payload",return_value=payload),\
             patch("social_adapters.buffer_three_channels.prepare",return_value={}),\
             patch.object(ig,"source_media_is_404",return_value=False),\
             patch.object(ig,"schedule",side_effect=TimeoutError("ambiguous")):
            with self.assertRaises(TimeoutError):ig.publish_once()
        self.assertEqual(actions,["lease","start","fail"])

    def test_never_conflate_transport_with_typed_rejection(self):
        code=(ROOT/'tools/cortes_buffer_pinterest_cloud.py').read_text(encoding='utf8')
        self.assertIn('except BufferDefiniteRejection as exc:',code)
        self.assertIn('queue("rejected",{**fence,"reason":exc.classification})',code)
        self.assertIn('notify_buffer_rejection_p0',code)
        self.assertIn('except Exception:',code)
        queue=(ROOT/'tools/cortes_queue_ha.py').read_text(encoding='utf8')
        self.assertIn('"buffer-rejected"',queue)
if __name__=='__main__':unittest.main()
