"""Contract tests: Pinterest local web lane, editorial gates and no unsafe API fallback."""
import unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.cortes_pinterest_browser_local import validate_job

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
    def test_neon_device_scoped_pinterest_actions(self):
        worker=(ROOT/"tools"/"cortes_pinterest_browser_local.py").read_text(encoding="utf-8")
        neon=(ROOT/"infra"/"neon-cortes-queue"/"index.mjs").read_text(encoding="utf-8")
        self.assertIn("crypto.timingSafeEqual",neon)
        self.assertIn(r'/^Bearer\s+([^\s]+)$/i',neon)
        self.assertNotIn(r'/^Bearer\\s+',neon)
        self.assertIn('"?action=browser-" + action',worker)
        self.assertIn("pinterestBrowserAction",neon)
        self.assertIn("r.ordinal > CASE WHEN r.weekday IN (1,2) THEN 15 ELSE 14 END",neon)
        self.assertIn("CORTES_DAILY_PUBLICATION", (ROOT/"db"/"migrations"/"20261021_cortes_daily_publication_limit_100.sql").read_text(encoding="utf-8"))
    def test_buffer_cannot_consume_browser_lane_when_old_fallback(self):
        buffer=(ROOT/"tools"/"cortes_buffer_pinterest_cloud.py").read_text(encoding="utf-8")
        self.assertIn('lease.get("delivery_route") != "buffer"',buffer)
    def test_isolated_cdp_and_orphan_cleanup(self):
        ui=(ROOT/"tools"/"cortes_pinterest_browser_ui.mjs").read_text(encoding="utf-8")
        self.assertIn("CORTES_CHROME_CDP_PORT||9226",ui)
        self.assertIn("pruneOwnedPinterestTabs",ui)
        self.assertIn("PINTEREST_BROWSER_ACCOUNT_NOT_VERIFIED",ui)
    def test_react_upload_input_remount_cannot_hide_ready_video_preview(self):
        ui=(ROOT/"tools"/"cortes_pinterest_browser_ui.mjs").read_text(encoding="utf-8")
        self.assertNotIn("f?.files?.length===1",ui)
        self.assertIn('videos.length>0&&ready',ui)
        self.assertIn('storyboard-drafts-sidebar',ui)

    def test_browser_uses_no_pinterest_api_or_login_bypass(self):
        ui=(ROOT/"tools"/"cortes_pinterest_browser_ui.mjs").read_text(encoding="utf-8")
        for forbidden in ("api.pinterest.com","PINTEREST_ACCESS_TOKEN","captcha_solver","stealth_plugin"):
            self.assertNotIn(forbidden,ui)
        self.assertIn("PINTEREST_BROWSER_LOGIN_REQUIRED",ui)
        self.assertIn("SUBMIT_CLICKED",ui)

if __name__=="__main__":unittest.main()
