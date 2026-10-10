#!/usr/bin/env python3
"""Fail-closed static contract: no public credential screenshots or ambiguous password fields."""
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

def src(path):return (ROOT/path).read_text(encoding="utf-8")

class KwaiCredentialSafetyTests(unittest.TestCase):
    def test_canonical_login_has_no_generic_password_fallback(self):
        s=src("tools/kwai_credential_login.py")
        self.assertIn("KWAI_PASSWORD_FIELD_NOT_VERIFIED",s)
        self.assertIn("if len(verified)!=1:",s)
        self.assertNotIn("es[-1] if es else None",s)
        self.assertNotIn("if es and ('password' in t",s)
    def test_alternate_login_has_explicit_password_field(self):
        s=src("kwai_android_autologin.py")
        self.assertIn("if not password_fields(dump()):",s)
        self.assertIn("fill_verified_password(PASSWORD)",s)
        self.assertNotIn("KWAI_POST_PROFILE_UI=",s)
        self.assertNotIn("KWAI_FILL_DEBUG_UI=",s)
    def test_headless_never_saves_login_screenshot(self):
        s=src("kwai_headless_login.sh")
        self.assertNotIn("screencap -p",s)
    def test_remote_login_never_saves_login_screenshot_or_xml(self):
        s=src("kwai_remote_android_login.sh")
        self.assertNotIn("screencap -p",s)
        self.assertNotIn("cp /tmp/kwai-ui.xml kwai-login-detected.xml",s)
    def test_queue_publisher_paused_until_rotation(self):
        s=src(".github/workflows/kwai-queue-publisher.yml")
        self.assertNotIn("cron:",s)
        self.assertIn("vars.KWAI_CREDENTIALS_ROTATED == 'true'",s)
        self.assertNotIn("kwai-headless-ready.png\n",s)
    def test_reconciliation_cannot_fabricate_remote_post_id(self):
        s=src("kwai_queue_state.sh")
        self.assertIn("KWAI_REMOTE_POST_ID must be independently observed",s)
        self.assertIn("RECONCILIATION_REMOTE_ID_INVALID",s)
        self.assertNotIn('"remote_id":"kwai:"+sys.argv[1]',s)
    def test_safe_android_diagnostic_uses_no_credentials(self):
        s=src(".github/workflows/kwai-native-login-targeted-diagnostic.yml")
        self.assertNotIn("secrets.KWAI_PASSWORD",s)
        self.assertNotIn("secrets.KWAI_LOGIN",s)

if __name__=="__main__":unittest.main()
