"""Daily secondary TikTok queue source must remain per-account and read-only."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"tools"/"cortes_tiktok_lucasrosalem4_manifest.py"
spec=importlib.util.spec_from_file_location("secondary_manifest",FILE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class TikTokSecondaryManifestContracts(unittest.TestCase):
    def test_source_is_signed_neon_only(self):
        self.assertTrue(m.SOURCE.startswith("https://"))
        self.assertEqual(m.ACCOUNT,"lucasrosalem4")
        self.assertEqual(m.AUDIENCE,"https://anthares-remote-primary.vercel.app/api/cortes-tiktok")

    def test_clip_validation(self):
        row={"segment_id":"g1:9CIk-I_3VhM:7216:7273",
             "source_id":"9CIk-I_3VhM",
             "media_url":"https://anthares.us/wp-content/uploads/anthares-clips/2026/10/test.mp4",
             "title":"A evolução dos atores",
             "duration_seconds":57}
        self.assertTrue(m.valid_clip(row))
        self.assertFalse(m.valid_clip({**row,"source_id":"mismatched"}))
        self.assertFalse(m.valid_clip({**row,"media_url":"https://another.invalid/clip.mp4"}))
        self.assertFalse(m.valid_clip({**row,"duration_seconds":120}))

    def test_authorization_is_required_before_request(self):
        from unittest.mock import patch
        with patch.dict(m.os.environ,{"GITHUB_REF":"refs/heads/main",
                                      "ACTIONS_ID_TOKEN_REQUEST_URL":"",
                                      "ACTIONS_ID_TOKEN_REQUEST_TOKEN":""},clear=True):
            with self.assertRaises(RuntimeError):
                m.oidc()

    def test_neon_deploy_has_read_only_action(self):
        source=(ROOT/"infra"/"neon-cortes-tiktok"/"index.mjs").read_text(encoding="utf-8")
        self.assertIn("action==='source-manifest'&&role==='consumer'",source)
        self.assertIn("cortes-tiktok-lucasrosalem4-manifest.yml",source)
        self.assertIn("status='confirmed'",source)


if __name__=="__main__":
    unittest.main()
