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

    def test_video_description_uses_draftjs_and_exact_readback(self):
        ui=(ROOT/"tools"/"cortes_pinterest_browser_ui.mjs").read_text(encoding="utf-8")
        self.assertIn('PIN_DESCRIPTION_EDITOR_NOT_READY',ui)
        self.assertIn('PIN_DESCRIPTION_NOT_VERIFIED',ui)
        self.assertIn('[aria-label="Descreva seu Pin"]',ui)

    def test_board_already_selected_must_match_exact_destination(self):
        ui=(ROOT/"tools"/"cortes_pinterest_browser_ui.mjs").read_text(encoding="utf-8")
        self.assertIn("if(already)return",ui)
        self.assertIn("storyboard-drafts-sidebar",ui)
        self.assertIn("norm(x.textContent)===expected",ui)

    def test_failed_or_missing_media_rotates_without_duplicating_pin(self):
        neon=(ROOT/"infra"/"neon-cortes-queue"/"index.mjs").read_text(encoding="utf-8")
        start=neon.index("async function pinterestBrowserAction")
        browser=neon[start:]
        self.assertIn("ORDER BY p.created_at,p.updated_at,p.id FOR UPDATE OF p SKIP LOCKED LIMIT 1",browser)
        self.assertIn("CASE WHEN publication_started_at IS NULL THEN 'queued' ELSE 'uncertain'",browser)

    def test_invalid_media_is_quarantined_without_blocking_queue(self):
        worker=(ROOT/"tools"/"cortes_pinterest_browser_local.py").read_text(encoding="utf-8")
        neon=(ROOT/"infra"/"neon-cortes-queue"/"index.mjs").read_text(encoding="utf-8")
        self.assertIn('media_missing(job["media_url"])', worker)
        self.assertIn('call("media-invalid", fence)', worker)
        self.assertIn('qa_media_incident(fence["id"]', worker)
        self.assertIn("status='leased'", neon)
        self.assertIn("publication_started_at IS NULL AND lease_owner=$3",neon)
        self.assertIn("source_media_invalid",neon)
        self.assertIn("pinterest_expired_after_next_day",neon)

    def test_next_day_retry_and_day_three_discard(self):
        neon=(ROOT/"infra"/"neon-cortes-queue"/"index.mjs").read_text(encoding="utf-8")
        beginning=neon.index("async function pinterestBrowserAction")
        end=neon.index("// Personal member publishing",beginning)
        browser=neon[beginning:end]
        self.assertIn("BETWEEN (now() AT TIME ZONE 'America/Campo_Grande')::date - 1",browser)
        self.assertIn("retry_after_date",browser)
        self.assertIn("status='failed'",browser)
        self.assertIn("ORDER BY p.created_at,p.updated_at,p.id",browser)

    def test_evening_fallback_maintains_atomic_neon_claim(self):
        neon=(ROOT/"infra"/"neon-cortes-queue"/"index.mjs").read_text(encoding="utf-8")
        chunk=neon[neon.index("async function pinterestBrowserAction"):]
        self.assertIn("extract(hour FROM now() AT TIME ZONE 'America/Campo_Grande') >= 21",chunk)
        self.assertIn("FOR UPDATE OF p SKIP LOCKED LIMIT 1",chunk)

    def test_pinterest_editor_diagnostic_never_copies_caption(self):
        ui=(ROOT/"tools"/"cortes_pinterest_browser_ui.mjs").read_text(encoding="utf-8")
        worker=(ROOT/"tools"/"cortes_pinterest_browser_local.py").read_text(encoding="utf-8")
        self.assertIn("PREPARE_DIAGNOSTIC",ui)
        self.assertIn('PINTEREST_EDITOR_DIAGNOSTIC',worker)
        self.assertIn('invalidCount',ui)
        self.assertNotIn("caption:data",ui)

    def test_browser_uses_no_pinterest_api_or_login_bypass(self):
        ui=(ROOT/"tools"/"cortes_pinterest_browser_ui.mjs").read_text(encoding="utf-8")
        for forbidden in ("api.pinterest.com","PINTEREST_ACCESS_TOKEN","captcha_solver","stealth_plugin"):
            self.assertNotIn(forbidden,ui)
        self.assertIn("PINTEREST_BROWSER_LOGIN_REQUIRED",ui)
        self.assertIn("SUBMIT_CLICKED",ui)

if __name__=="__main__":unittest.main()
