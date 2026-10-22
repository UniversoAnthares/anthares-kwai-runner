"""No media loss, no Pinterest draft overflow, safe cross-provider ledger."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class PinterestProtection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.js=(ROOT/"tools"/"cortes_pinterest_browser_ui.mjs").read_text(encoding="utf8")
        cls.worker=(ROOT/"tools"/"cortes_pinterest_browser_local.py").read_text(encoding="utf8")
        cls.queue=(ROOT/"infra"/"neon-cortes-queue"/"index.mjs").read_text(encoding="utf8")

    def test_no_upload_after_desktop_50_drafts(self):
        self.assertIn("auth.draftCount>=49",self.js)
        self.assertIn("PIN_DRAFT_CAPACITY_EXHAUSTED",self.js)
        self.assertIn("draft_count:auth.draftCount",self.js)
        self.assertIn("PINTEREST_DRAFT_CAPACITY_PAUSED",self.worker)
        self.assertLess(self.worker.index("PINTEREST_DRAFT_CAPACITY_PAUSED"),self.worker.index('leased = call("lease"'))

    def test_no_premature_next_day_discard(self):
        browser=self.queue[self.queue.index("async function pinterestBrowserAction"): ]
        self.assertIn("source_media_expired_next_day",browser)
        self.assertIn("status='failed' AND remote_id IS NULL",browser)
        self.assertIn("status='queued'",browser)
        self.assertIn("retry_after_at",browser)
        self.assertIn("AT TIME ZONE 'UTC'",browser)
        self.assertIn("now()+interval '90 minutes'",browser)
        self.assertIn("::date - 1",browser)
        self.assertIn("publication_started_at IS NULL AND lease_owner=$3",browser)

    def test_expired_leases_are_fenced_for_duplicate_safety(self):
        b=self.queue[self.queue.index("async function pinterestBrowserAction"): ]
        self.assertIn("publication_started_at IS NULL THEN 'queued' ELSE 'uncertain'",b)
        self.assertIn("'pinterest_expired_after_start'",b)
        self.assertIn("lease_until < now()",b)
        self.assertIn("FOR UPDATE OF p SKIP LOCKED LIMIT 1",b)

    def test_buffer_media_isolated_and_pending_readbacks_not_starved(self):
        buff=self.queue[self.queue.index("async function bufferAction"):self.queue.index("/** Device-authenticated Pinterest")]
        self.assertIn("PINTEREST_MEDIA_MISSING_FENCE_REJECTED",buff)
        self.assertIn("ORDER BY updated_at ASC LIMIT 25",buff)
        self.assertIn("retry_after_at",buff)

    def test_central_qa_tickets_are_deduplicated(self):
        self.assertIn("QA-P0-FINGERPRINT:",self.worker)
        self.assertIn("pinterest-p0-",self.worker)

if __name__=="__main__": unittest.main()
