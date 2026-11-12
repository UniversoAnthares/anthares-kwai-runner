"""Offline regression for independent Neon/Cloudflare pacing receipts."""
from datetime import datetime,timezone
from pathlib import Path
import importlib.util,unittest

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"tools"/"cortes_tiktok_pacing_receipt_watch.py"

class PacingReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sys
        sys.path.insert(0,str(ROOT/"tools"))
        spec=importlib.util.spec_from_file_location("pacing_receipts",SRC)
        cls.mod=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def valid(self):
        return {
            "ok":True,"account":"universo.anthares","timezone":"America/Campo_Grande",
            "guards_active":True,"guards":{x:"O" for x in self.mod.EXPECTED_GUARDS},
            "starts":[{"utc":"2026-11-13T10:00:00Z","local_time":"06:00:00.000000"},
                      {"utc":"2026-11-13T22:00:00Z","local_time":"18:00:00.000000"}],
            "local_day":"2026-11-13","started_today":2,"capacity_used":2,
            "legacy_pre_guard_count":0,"governed_start_count":2,
            "window_violation_count":0,"server_now":"2026-11-13T22:30:00Z",
            "mode":"paced","next_due":"2026-11-13T23:00:00Z",
        }

    def test_clean_receipts(self):
        self.assertEqual(self.mod.check(self.valid())["started"],2)

    def test_wrong_local_hour(self):
        r=self.valid();r["starts"][0]["local_time"]="05:00:00.000000"
        with self.assertRaises(AssertionError):
            self.mod.check(r)

    def test_missing_guard(self):
        r=self.valid();r["guards"]["cortes_tiktok_hard_window_06_23_v1"]="D"
        with self.assertRaises(AssertionError):
            self.mod.check(r)

    def test_quota_ceiling(self):
        r=self.valid();r["started_today"]=101
        with self.assertRaises(AssertionError):
            self.mod.check(r)

    def test_window_is_hard_not_discretionary(self):
        r=self.valid();r["starts"][0]["utc"]="2026-11-13T09:59:00Z"
        r["starts"][0]["local_time"]="05:59:00.000000"
        with self.assertRaises(AssertionError):
            self.mod.check(r)

    def test_neon_ingress_has_only_read_only_audit(self):
        source=(ROOT/"infra"/"neon-cortes-tiktok"/"index.mjs").read_text()
        self.assertIn("action==='pacing-audit'&&role==='consumer'",source)
        self.assertIn("export async function pacingAudit()",source)
        self.assertIn("guardsActive",source)
        self.assertIn("clock.rows[0].local_day",source)
        self.assertNotIn("INSERT INTO",source[source.index("export async function pacingAudit()"):source.index("async function handler(req,res)")])

if __name__=="__main__":unittest.main()
