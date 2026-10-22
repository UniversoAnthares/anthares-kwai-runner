"""No blind retries: public Pin readback must be fenced to existing Buffer job."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class PublicBufferReconciliation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.neon=(ROOT/"infra/neon-cortes-queue"/"index.mjs").read_text(encoding="utf8")
        cls.local=(ROOT/"tools"/"cortes_pinterest_browser_local.py").read_text(encoding="utf8")
        cls.client=(ROOT/"tools"/"cortes_pinterest_public_buffer_reconcile.py").read_text(encoding="utf8")
        cls.node=(ROOT/"tools"/"cortes_pinterest_public_pin_readback.mjs").read_text(encoding="utf8")
    def test_device_and_existing_scheduled_cas_required(self):
        b=self.neon[self.neon.index("async function pinterestBrowserAction"):]
        self.assertLess(b.index("WRONG_BROWSER_OWNER"),b.index("if(verb==='reconcile-buffer')"))
        self.assertIn("p.status='uncertain'",b)
        self.assertIn("p.remote_id=$3",b)
        self.assertIn("p.payload->>'media_url'=$4",b)
        self.assertIn("p.confirmation_evidence->>'kind'='buffer_scheduled'",b)
        self.assertIn("BUFFER_PUBLIC_PROOF_CAS_REJECTED",b)
        self.assertIn("other.id<>$1",b)
    def test_public_url_account_board_duration_verified(self):
        self.assertIn("verified_public_board",self.client)
        self.assertIn("abs(src_ms-pub_ms)>120",self.client)
        self.assertIn("PINTEREST_SOURCE_IDENTITY_INVALID",self.client)
        self.assertIn("PINTEREST_PUBLIC_SOURCE_MISMATCH",self.client)
        self.assertIn("PINTEREST_PUBLIC_PROOF_INVALID",self.neon)
        self.assertIn("public_duration_ms",self.node)
        self.assertIn("document.querySelectorAll",self.node)
    def test_read_only_browser_no_publish_and_owned_tabs_closed(self):
        self.assertIn("/json/close/",self.node)
        self.assertNotIn("DOM.setFileInputFiles",self.node)
        self.assertNotIn("SUBMIT_CLICKED",self.node)
        self.assertIn("reconcile-buffer",self.local)
    def test_cli_dryrun_never_modifies_ledger(self):
        self.assertIn("if not a.commit:",self.client)
        self.assertIn("call('reconcile-buffer'",self.client)
        self.assertIn("neon_write",self.client)

if __name__=='__main__':unittest.main()
