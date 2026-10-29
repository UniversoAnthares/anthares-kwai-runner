"""Secondary TikTok source is remote-only, isolated and verified read-only."""
import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "tools" / "cortes_tiktok_lucasrosalem4_manifest.py"
spec = importlib.util.spec_from_file_location("secondary_manifest", FILE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

CLIP = {"segment_id": "g1:9CIk-I_3VhM:7216:7273",
        "source_id": "9CIk-I_3VhM",
        "media_url": "https://anthares.us/wp-content/uploads/anthares-clips/2026/10/test.mp4",
        "title": "A evolução dos atores",
        "duration_seconds": 57}
DAY = "2026-10-29"


def source(clips=None):
    rows = [CLIP] if clips is None else clips
    return {"ok": True, "account": m.ACCOUNT, "date": DAY,
            "clip_count": len(rows), "clips": rows}


class TikTokSecondaryManifestContracts(unittest.TestCase):
    def test_source_is_signed_neon_only(self):
        self.assertTrue(m.SOURCE.startswith("https://"))
        self.assertEqual(m.ACCOUNT, "lucasrosalem4")
        self.assertEqual(m.AUDIENCE, "https://anthares-remote-primary.vercel.app/api/cortes-tiktok")

    def test_clip_validation(self):
        self.assertTrue(m.valid_clip(CLIP))
        self.assertFalse(m.valid_clip({**CLIP, "source_id": "mismatched"}))
        self.assertFalse(m.valid_clip({**CLIP, "media_url": "https://another.invalid/clip.mp4"}))
        self.assertFalse(m.valid_clip({**CLIP, "duration_seconds": 120}))

    def test_authorization_is_required_before_request(self):
        with patch.dict(m.os.environ, {"GITHUB_REF": "refs/heads/main",
                                       "ACTIONS_ID_TOKEN_REQUEST_URL": "",
                                       "ACTIONS_ID_TOKEN_REQUEST_TOKEN": ""}, clear=True):
            with self.assertRaises(RuntimeError):
                m.oidc()

    def test_neon_deploy_has_read_only_action(self):
        script = (ROOT / "infra" / "neon-cortes-tiktok" / "index.mjs").read_text(encoding="utf-8")
        self.assertIn("action==='source-manifest'&&role==='consumer'", script)
        self.assertIn("cortes-tiktok-lucasrosalem4-manifest.yml", script)
        self.assertIn("status='confirmed'", script)

    def test_verified_remote_count_and_day(self):
        self.assertEqual(m.validate_remote_manifest(source(), DAY), {"day": DAY, "count": 1})
        self.assertEqual(m.validate_remote_manifest(source([]), DAY), {"day": DAY, "count": 0})

    def test_fails_closed_on_wrong_account_day_or_count(self):
        for payload in ({**source(), "account": "universo.anthares"},
                        {**source(), "date": "2026-10-28"},
                        {**source(), "clip_count": 2},
                        {**source(), "clips": [{}]}):
            with self.subTest(payload=payload.get("account", "invalid")):
                with self.assertRaises(RuntimeError):
                    m.validate_remote_manifest(payload, DAY)

    def test_duplicate_clip_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "DUPLICATE_SEGMENT"):
            m.validate_remote_manifest(source([CLIP, CLIP]), DAY)

    def test_execution_only_reads_remote_source_without_writing(self):
        with patch.object(m, "oidc", return_value="mock-signed-token"), \
             patch.object(m, "request_json", return_value=source()) as fetch, \
             patch.object(m, "validate_remote_manifest", wraps=m.validate_remote_manifest) as validate, \
             patch.object(m, "datetime") as clock, \
             patch.object(m.os, "replace", create=True) as local_write, \
             patch.object(m, "open", create=True) as file_write, \
             contextlib.redirect_stdout(io.StringIO()) as output:
            # The date gate is explicitly supplied by the provider in production.
            clock.now.return_value.strftime.return_value = DAY
            self.assertEqual(m.main(), 0)
            self.assertIn("storage=remote_only read_only=1", output.getvalue())
            fetch.assert_called_once_with(m.SOURCE + "?action=source-manifest", "mock-signed-token")
            validate.assert_called_once()
            local_write.assert_not_called()
            file_write.assert_not_called()

    def test_script_does_not_depend_on_local_manifest_path(self):
        body = FILE.read_text(encoding="utf-8")
        for prohibited in ("secondary-publisher", "queue-manifest.json", "NamedTemporaryFile",
                           "os.replace(", "HOME.mkdir(", "WINDOWS_RUNNER_REQUIRED"):
            self.assertNotIn(prohibited, body)


if __name__ == "__main__":
    unittest.main()
