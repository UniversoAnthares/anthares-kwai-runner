"""Regression gates for TikTok durability; requires no live token or uploads."""
import pathlib
import unittest
from unittest.mock import patch
from urllib.error import URLError
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]

class TikTokRecoverySafety(unittest.TestCase):
    def test_atomic_started_budget_is_serialized_per_day(self):
        code=(ROOT/"vercel-ara-primary/api/cortes-tiktok.mjs").read_text(encoding="utf-8")
        self.assertIn("pg_advisory_xact_lock",code)
        self.assertIn("publication_started_at AT TIME ZONE 'America/Campo_Grande'",code)
        self.assertIn("daily_publication_start_limit_100",code)
        self.assertIn("await client.query('BEGIN')",code)
        self.assertIn("await client.query('COMMIT')",code)
        self.assertIn("await client.query('ROLLBACK')",code)
        self.assertIn("publication_started_at IS NULL RETURNING id,status,lease_generation",code)
        self.assertNotIn("COUNT(*) FILTER (WHERE status='confirmed' AND (confirmed_at",code)

    def test_prestart_requeue_is_cooled_and_uncertain_remains_fenced(self):
        code=(ROOT/"vercel-ara-primary/api/cortes-tiktok.mjs").read_text(encoding="utf-8")
        self.assertIn("retry_not_before<=now()",code)
        self.assertIn("preflight_failures+1",code)
        self.assertIn("publication_started_at IS NULL THEN 'queued' ELSE 'uncertain'",code)
        hosted=(ROOT/"tools/cortes_tiktok_hosted_publish.py").read_text(encoding="utf-8")
        self.assertIn("media_preflight_failed_before_start",hosted)
        self.assertIn("after_started_requires_reconciliation",hosted)

    def test_browser_and_recovery_triggers_are_independent(self):
        code=(ROOT/".github/workflows/cortes-tiktok-publisher.yml").read_text(encoding="utf-8")
        self.assertIn("schedule:",code)
        self.assertIn("followup:",code)
        self.assertIn("CORTES_TIKTOK_PLAYWRIGHT_ALT_CDN_FALLBACK",code)
        self.assertIn("qa_tiktok_p0:",code)

    def test_media_download_retries_with_official_alternate_hostname(self):
        import sys
        sys.path.insert(0,str(ROOT/"tools"))
        import cortes_tiktok_hosted_publish as hosted
        job={"media_url":"https://anthares.us/short.mp4"}
        urls=[]
        class Response:
            headers={"Content-Type":"video/mp4"}
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def read(self,size):return b"x"*32768 if not hasattr(self,"read_once") and setattr(self,"read_once",True) is None else b""
        def fake_open(req,timeout=0):
            urls.append(req.full_url)
            if len(urls)<3:raise URLError("transient")
            return Response()
        with TemporaryDirectory() as root:
            with patch("urllib.request.urlopen",side_effect=fake_open),patch("time.sleep",return_value=None):
                hosted.download_verified(job,pathlib.Path(root)/"video.mp4")
        self.assertEqual(len(urls),3)
        self.assertEqual(urlsplit(urls[-1]).hostname,"www.anthares.us")

if __name__=="__main__":
    unittest.main()
