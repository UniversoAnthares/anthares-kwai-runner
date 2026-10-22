"""Bounded same-night LinkedIn queue drain must expire exactly 05:00 local."""
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from unittest.mock import patch
from tools import cortes_linkedin_personal_cloud as personal
from tools import cortes_buffer_linkedin_cloud as corporate
ROOT=Path(__file__).resolve().parents[1]

class Deadline(unittest.TestCase):
    def test_dynamic_control_and_expiry_present(self):
        js=(ROOT/"infra/neon-cortes-queue/index.mjs").read_text(encoding="utf-8")
        self.assertIn("LINKEDIN_EXCEPTION_START",js)
        self.assertIn("2026-10-21 22:45:00",js)
        self.assertIn("2026-10-22 05:00:00",js)
        self.assertIn("created_at >= ${LINKEDIN_EXCEPTION_START}",js)
        self.assertIn("created_at >= ${cutoffForBuffer}",js)
    def test_batch_limited_for_both_accounts(self):
        for fn in (personal,corporate):
            self.assertTrue(callable(fn.exception_active))
        self.assertIn("batch_size = 2 if exception_active() else 1",Path(personal.__file__).read_text())
        self.assertIn("batch_size=2 if exception_active() else 1",Path(corporate.__file__).read_text())
    def test_wall_clock_timezone_and_auto_expiry(self):
        for fn in (personal,corporate):
            s=Path(fn.__file__).read_text()
            self.assertIn('ZoneInfo("America/Campo_Grande")',s)
            self.assertIn("2026,10,22,5,0",s.replace(" ",""))

if __name__=="__main__":unittest.main()
