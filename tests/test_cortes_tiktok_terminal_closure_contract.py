"""Safety contract: October 27 historic uncertainty is archived, not retransmitted."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class TerminalClosureContract(unittest.TestCase):
    def test_migration_is_exact_scoped_audited_and_idempotent(self):
        sql=(ROOT/"db/migrations/20261112_tiktok_historical_uncertain_terminal_close.sql").read_text()
        for phrase in (
            "v_open<>10", "v_closed<>0", "v_inserted<>10", "v_updated<>10",
            "evidence_run_id", "43329490208", "A7BsgCe3-oo",
            "lease_until IS NULL", "remote_id IS NULL", "confirmed_at IS NULL",
            "UPDATE public.cortes_tiktok_publications",
            "closed_unverified_no_reupload", "inventory_complete",
            "IF v_open=0 AND v_closed=10 THEN"
        ):
            self.assertIn(phrase,sql)
        self.assertNotIn("status='confirmed'",sql)
        self.assertNotIn("status='queued'",sql)

    def test_ingresses_preserve_closed_status_and_enqueue_deduplication(self):
        for path in ("infra/neon-cortes-tiktok/index.mjs","vercel-ara-primary/api/cortes-tiktok.mjs"):
            source=(ROOT/path).read_text()
            self.assertIn("closed_unverified",source)
            self.assertIn("ON CONFLICT(segment_id) DO NOTHING",source)
            self.assertIn("status=\\'queued\\'",source)

    def test_studio_audit_stops_after_terminal_close(self):
        s=(ROOT/"tools/cortes_tiktok_uncertain_batch_audit.py").read_text()
        self.assertIn("CORTES_TIKTOK_HISTORIC_UNCERTAIN_TERMINALLY_CLOSED_NO_REUPLOAD",s)
        self.assertIn('current=qcall("status",oidc())',s)
        self.assertLess(s.index('current=qcall("status",oidc())'),s.index("state=preflight_vault()"))

if __name__ == "__main__":
    unittest.main()
