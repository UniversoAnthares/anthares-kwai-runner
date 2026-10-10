#!/usr/bin/env python3
"""Deterministic tests derived from redacted UIAutomator evidence in run 38062865655."""
import importlib.util
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOCATOR = ROOT / "tools" / "kwai_login_ui_locator.py"
spec = importlib.util.spec_from_file_location("kwai_login_ui_locator", LOCATOR)
selector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selector)

# Synthetic minimal fixture uses exact public resource IDs and bounds observed
# in a real Kwai native login chooser, with no account data or session contents.
CHOOSER = """<hierarchy>
<node class="android.widget.TextView" resource-id="com.kwai.video.basis:id/login_label" text="Create your profile" bounds="[70,734][763,845]" />
<node class="android.view.ViewGroup" resource-id="com.kwai.video.basis:id/login_platform_item_layout" clickable="true" bounds="[70,1108][1010,1233]" />
<node class="android.widget.TextView" resource-id="com.kwai.video.basis:id/login_platform_item_text" text="Continue with Google" bounds="[353,1144][728,1197]" />
<node class="android.widget.TextView" resource-id="com.kwai.video.basis:id/login_platform_expand_text" text="or use Facebook  |  Phone  |  Email" bounds="[265,1285][815,1376]" />
<node class="android.widget.FrameLayout" resource-id="com.kwai.video.basis:id/id_home_bottom_tab_me" clickable="true" bounds="[864,2123][1080,2274]" />
</hierarchy>"""
FORM = """<hierarchy>
<node class="android.widget.TextView" text="Log in with Email" bounds="[0,0][1080,150]" />
<node class="android.widget.EditText" resource-id="com.kwai.video:id/login_email_input" bounds="[50,250][1030,350]" />
<node class="android.widget.EditText" resource-id="com.kwai.video:id/login_password_input" password="true" bounds="[50,400][1030,500]" />
</hierarchy>"""


class KwaiNativeLoginSelectorTests(unittest.TestCase):
    def test_chooser_is_not_form(self):
        self.assertFalse(selector.email_form_visible(selector.parse(CHOOSER)))

    def test_chooser_is_detected(self):
        self.assertTrue(selector.native_chooser_visible(selector.parse(CHOOSER)))

    def test_email_sub_action_hits_rightmost_segment(self):
        x, y = selector.email_entry(selector.parse(CHOOSER))
        self.assertGreaterEqual(x, 715)
        self.assertLessEqual(x, 815)
        self.assertEqual(y, 1330)

    def test_google_chooser_coordinates(self):
        self.assertEqual(selector.google_entry(selector.parse(CHOOSER)), (540, 1170))

    def test_profile_tab_coordinates(self):
        self.assertEqual(selector.profile_tab(selector.parse(CHOOSER)), (972, 2198))

    def test_form_requires_real_edittext(self):
        self.assertTrue(selector.email_form_visible(selector.parse(FORM)))

    def test_no_email_entry_when_form_open(self):
        self.assertIsNone(selector.email_entry(selector.parse(FORM)))

    def test_search_box_is_not_login(self):
        xml = '<hierarchy><node class="android.widget.EditText" resource-id="com.kwai.video:id/search_box" text="Search" bounds="[0,0][500,80]" /></hierarchy>'
        self.assertFalse(selector.email_form_visible(selector.parse(xml)))

    def test_invalid_chooser_bounds_are_not_tapped(self):
        xml = CHOOSER.replace("[265,1285][815,1376]", "[815,1376][265,1285]")
        self.assertIsNone(selector.email_entry(selector.parse(xml)))

    def test_e_mail_localization(self):
        xml = CHOOSER.replace("Email", "E-mail")
        self.assertTrue(selector.native_chooser_visible(selector.parse(xml)))
        self.assertIsNotNone(selector.email_entry(selector.parse(xml)))

    def test_missing_chooser_no_tap(self):
        self.assertIsNone(selector.email_entry(selector.parse('<hierarchy/>')))

    def test_malformed_xml_fails_closed(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", encoding="utf-8") as fh:
            fh.write("<hierarchy><broken")
            fh.flush()
            proc = subprocess.run([sys.executable, str(LOCATOR), "email-entry", fh.name], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            self.assertFalse(proc.stdout)

    def test_cli_chooser_form_false(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", encoding="utf-8") as fh:
            fh.write(CHOOSER)
            fh.flush()
            proc = subprocess.run([sys.executable, str(LOCATOR), "email-form", fh.name], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)

    def test_cli_email_coordinates(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", encoding="utf-8") as fh:
            fh.write(CHOOSER)
            fh.flush()
            proc = subprocess.run([sys.executable, str(LOCATOR), "email-entry", fh.name], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(len(proc.stdout.split()), 2)

    def test_script_does_not_blindly_retry_google(self):
        text = (ROOT / "kwai_remote_android_login.sh").read_text()
        self.assertNotIn("seq 1 24", text)
        self.assertIn('KWAI_LOGIN_METHOD:-email', text)
        self.assertIn('KWAI_NATIVE_LOGIN_CHOOSER_DETECTED', text)
        self.assertIn('KWAI_LOGIN_DEADLINE_SECONDS:-180', text)


if __name__ == "__main__":
    unittest.main()
