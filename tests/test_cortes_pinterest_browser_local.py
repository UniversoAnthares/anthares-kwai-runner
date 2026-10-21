"""Contract tests: Pinterest local web lane, editorial gates and no unsafe API fallback."""
import unittest
from pathlib import Path
from tools.cortes_pinterest_browser_local import validate_job

ROOT=Path(__file__).resolve().parents[1]

def job(payload=None):
    body={"platform":"pinterest","account_id":"lucasyahn",
          "media_url":"https://anthares.us/wp-content/uploads/anthares-clips/2026/10/short_test.mp4",
          "duration_seconds":58,
          "title":"A Metamorfose [Kafka] - ANALISE | Trecho 10:25",
          "description":"Literatura e analise"}
    body.update(payload or {})
    return {"target_key":"pinterest:lucasyahn","duration_class":"short","payload":body}

class PinterestBrowserContract(unittest.TestCase):
    def test_weekly_buffer_slots_exactly_100(self):
        self.assertEqual(sum(15 if weekday in (1,2) else 14 for weekday in range(1,8)),100)
    def test_metadata_safe(self):
        result=validate_job(job())
        self.assertEqual(result["account_id"],"lucasyahn")
        self.assertTrue(result["title"].endswith(" ● Universo Anthares"))
        self.assertIn("www.anthares.us",result["description"])
    def test_never_publish_wrong_account(self):
        with self.assertRaises(ValueError):validate_job(job({"account_id":"other"}))
    def test_reject_wrong_host(self):
        with self.assertRaises(ValueError):validate_job(job({"media_url":"https://evil.test/video.mp4"}))
    def test_reject_bad_duration(self):
        with self.assertRaises(ValueError):validate_job(job({"duration_seconds":120}))
    def test_lease_atomic_lane_required(self):
        worker=(ROOT/"tools"/"cortes_pinterest_browser_local.py").read_text(encoding="utf-8")
        vercel=(ROOT/"vercel-ara-primary"/"api"/"cortes-queue.mjs").read_text(encoding="utf-8")
        neon=(ROOT/"infra"/"neon-cortes-queue"/"index.mjs").read_text(encoding="utf-8")
        self.assertIn('leased.get("delivery_route") != "browser"',worker)
        self.assertIn("FOR UPDATE OF p SKIP LOCKED",vercel)
        self.assertIn("pinterestRoutedLease",vercel)
        self.assertIn("15 ELSE 14 END",neon)
    def test_browser_uses_no_pinterest_api_or_login_bypass(self):
        ui=(ROOT/"tools"/"cortes_pinterest_browser_ui.mjs").read_text(encoding="utf-8")
        for forbidden in ("api.pinterest.com","PINTEREST_ACCESS_TOKEN","captcha_solver","stealth_plugin"):
            self.assertNotIn(forbidden,ui)
        self.assertIn("PINTEREST_BROWSER_LOGIN_REQUIRED",ui)
        self.assertIn("SUBMIT_CLICKED",ui)

if __name__=="__main__":unittest.main()
