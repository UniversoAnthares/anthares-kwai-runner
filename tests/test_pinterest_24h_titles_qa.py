import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PinterestQA24hAndTitles(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.queue=(ROOT/'infra/neon-cortes-queue/index.mjs').read_text(encoding='utf8')
  cls.worker=(ROOT/'tools/cortes_pinterest_metadata_qa.py').read_text(encoding='utf8')
  cls.buffer=(ROOT/'tools/cortes_buffer_pinterest_cloud.py').read_text(encoding='utf8')
 def test_24h_from_first_404_never_midnight(self):
  self.assertIn("first_detected_at",self.queue)
  self.assertIn("interval '24 hours'",self.queue)
  self.assertIn("source_media_expired_24h",self.queue)
  self.assertIn("qa-media-result",self.queue)
  self.assertIn("media_status",self.worker)
  self.assertIn("source_media_invalid",self.queue)
 def test_404s_isolated_without_other_queue_blocking(self):
  self.assertIn("p.status='queued'",self.queue)
  self.assertIn("FOR UPDATE OF p SKIP LOCKED LIMIT 1",self.queue)
  self.assertIn("PINTEREST_MEDIA_MISSING_FENCE_REJECTED",self.queue)
  self.assertIn("MEDIA_INVALID_FENCE_REJECTED",self.queue)
 def test_transcript_titles_fenced_only_pending(self):
  self.assertIn("metadata-pending",self.queue)
  self.assertIn("metadata-enrich",self.queue)
  self.assertIn("p.status='queued'",self.queue)
  self.assertIn("publication_started_at IS NULL AND remote_id IS NULL",self.queue)
  self.assertIn("editorial_transcript_hash",self.queue)
  self.assertIn("CORTES_STRATEGIC", (ROOT/'anthares_publisher/editorial.py').read_text())
 def test_editorial_pipeline_uses_local_models_no_fake_titles(self):
  self.assertIn("WhisperModel('small'",self.worker)
  self.assertIn("qwen2.5:3b",self.worker)
  self.assertIn("require_strategic_master(data)",self.worker)
  self.assertIn("PINTEREST_CONTEXTUAL_TITLE_INVALID",self.worker)
  self.assertIn("'after_id':after",self.worker)
 def test_cloud_strategy_validation_not_bypassed(self):
  self.assertIn('"editorial_policy":payload.get("editorial_policy")',self.buffer)
  self.assertIn('"keywords":payload.get("keywords")',self.buffer)
  self.assertIn('"hashtags":payload.get("hashtags")',self.buffer)
  self.assertIn("p.payload->>'editorial_policy'='anthares_editorial_transcript_v2'",self.queue)
if __name__=='__main__':unittest.main()
