"""P0 QA: soft 502 or "green" CI with zero daily Neon masters is urgent."""
import datetime as dt
import importlib.util
from pathlib import Path
from unittest.mock import patch
import unittest

PATH=Path(__file__).resolve().parents[1]/"tools/cortes_qa_p0_router.py"
spec=importlib.util.spec_from_file_location("cortes_qa_daily_round",PATH)
router=importlib.util.module_from_spec(spec)
spec.loader.exec_module(router)

class DailyRoundP0(unittest.TestCase):
    def test_no_masters_after_seven_creates_immediate_fingerprinted_p0(self):
        now=dt.datetime(2026,10,22,12,0,tzinfo=dt.timezone.utc)
        with patch.object(router,"NOW",now),patch.object(router,"http",return_value={
                "ok":True,"round_timezone":"America/Campo_Grande","today_master_count":0}):
            incidents=router.daily_round_incidents()
        self.assertEqual(len(incidents),1)
        self.assertEqual(incidents[0]["stage"],"P0_DAILY_PRODUCER_ZERO_MASTERS")
        self.assertIn("502",incidents[0]["description"])
        self.assertEqual(len(incidents[0]["id"]),24)

    def test_real_master_zero_alert_clears_without_ticket(self):
        now=dt.datetime(2026,10,22,12,0,tzinfo=dt.timezone.utc)
        with patch.object(router,"NOW",now),patch.object(router,"http",return_value={
                "ok":True,"round_timezone":"America/Campo_Grande","today_master_count":1}):
            self.assertEqual(router.daily_round_incidents(),[])

    def test_pre_seven_does_not_alarm(self):
        now=dt.datetime(2026,10,22,10,30,tzinfo=dt.timezone.utc)
        with patch.object(router,"NOW",now),patch.object(router,"http") as h:
            self.assertEqual(router.daily_round_incidents(),[])
            h.assert_not_called()

    def test_rejected_unverifiable_neon_health_never_silently_passes(self):
        now=dt.datetime(2026,10,22,12,0,tzinfo=dt.timezone.utc)
        with patch.object(router,"NOW",now),patch.object(router,"http",return_value={"ok":True,"today_master_count":"0"}):
            with self.assertRaisesRegex(RuntimeError,"HEALTH_INVALID"):
                router.daily_round_incidents()

if __name__=="__main__":unittest.main()
