#!/usr/bin/env python3
"""Regression contract for the Kwai native chooser -> credential form handoff.

Runs without Android or credentials; mocks only the ADB/UI boundary.
"""
import contextlib
import io
import os
import pathlib
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

source = os.environ.get("KWAI_CANONICAL_SOURCE", str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, source)
sys.path.insert(0, source + "/tools")
import kwai_android_login_entry as entry
from kwai_login_ui_locator import email_form_visible, native_chooser_visible, email_entry

EMPTY = "<hierarchy><node class='android.widget.TextView' text='Home' bounds='[0,0][100,100]'/></hierarchy>"
CHOOSER = """<hierarchy>
<node class="android.widget.TextView" resource-id="com.kwai.video:id/login_platform_expand_text" text="or use Facebook  |  Phone  |  Email" bounds="[265,1285][815,1376]"/>
</hierarchy>"""
FORM = """<hierarchy>
<node class="android.widget.TextView" text="Log in with Email" bounds="[0,0][1080,150]"/>
<node class="android.widget.EditText" resource-id="com.kwai.video:id/login_email_input" bounds="[50,250][1030,350]"/>
<node class="android.widget.EditText" resource-id="com.kwai.video:id/login_password_input" bounds="[50,400][1030,500]"/>
</hierarchy>"""
INTEREST = """<hierarchy>
<node class="android.view.View" resource-id="com.kwai.video:id/interest_tag_container" bounds="[0,0][1080,1920]"/>
<node class="android.widget.TextView" resource-id="com.kwai.video:id/bt_interest_skip_top_right" text="Skip" bounds="[900,0][1080,90]"/>
</hierarchy>"""
SEMANTIC = """<hierarchy>
<node class="android.widget.TextView" text="Email" bounds="[700,1285][815,1376]"/>
</hierarchy>"""
SEARCH = """<hierarchy>
<node class="android.widget.EditText" resource-id="com.kwai.video:id/search_box" bounds="[0,0][1080,90]"/>
</hierarchy>"""

def snapshot(xml):
    return list(ET.fromstring(xml).iter("node")), xml

class KwaiLoginHandoffTests(unittest.TestCase):
    def run_entry(self, frames, mode="email", environ=None):
        stdout = io.StringIO()
        with patch.object(entry, "snapshot", side_effect=[snapshot(f) for f in frames]) as snap, \
             patch.object(entry, "adb", return_value=b"") as adb, \
             patch.object(entry.time, "sleep") as sleep, \
             patch.object(sys, "argv", ["kwai_android_login_entry.py", mode]), \
             patch.dict(os.environ, environ or {}, clear=False), \
             contextlib.redirect_stdout(stdout):
            code = entry.main()
        taps = [c for c in adb.call_args_list if c.args[:3] == ("shell", "input", "tap")]
        return code, stdout.getvalue(), taps, snap.call_count, sleep.call_count

    def test_existing_form_short_circuit(self):
        rc, log, taps, _, _ = self.run_entry([FORM])
        self.assertEqual(rc, 0)
        self.assertIn("ALREADY_VISIBLE", log)
        self.assertEqual(taps, [])

    def test_chooser_immediately_to_form(self):
        rc, log, taps, _, _ = self.run_entry([CHOOSER, FORM])
        self.assertEqual(rc, 0)
        self.assertIn("KWAI_NATIVE_LOGIN_FORM_VISIBLE", log)
        self.assertEqual(len(taps), 1)

    def test_transient_blank_twice_before_chooser(self):
        rc, log, taps, reads, _ = self.run_entry([EMPTY, EMPTY, CHOOSER, FORM])
        self.assertEqual(rc, 0)
        self.assertEqual(reads, 4)
        self.assertEqual(len(taps), 1)

    def test_transient_blank_then_form_without_tap(self):
        rc, log, taps, _, _ = self.run_entry([EMPTY, FORM])
        self.assertEqual(rc, 0)
        self.assertEqual(taps, [])

    def test_six_empty_retries_fail_closed(self):
        rc, log, taps, reads, _ = self.run_entry([EMPTY] * 7)
        self.assertEqual(rc, 3)
        self.assertIn("CHOOSER_ABSENT", log)
        self.assertEqual(taps, [])
        self.assertEqual(reads, 7)

    def test_chooser_tapped_but_form_absent(self):
        rc, log, taps, reads, _ = self.run_entry([CHOOSER] * 6)
        self.assertEqual(rc, 4)
        self.assertIn("METHOD_NO_FORM", log)
        self.assertEqual(len(taps), 1)
        self.assertEqual(reads, 6)

    def test_interest_onboarding_then_chooser(self):
        rc, log, taps, _, _ = self.run_entry([INTEREST, CHOOSER, FORM])
        self.assertEqual(rc, 0)
        self.assertIn("INTEREST_ONBOARDING_SKIPPED", log)
        self.assertEqual(len(taps), 2)

    def test_semantic_fallback_uses_xml(self):
        with patch.object(entry, "method_coords", return_value=None):
            rc, log, taps, _, _ = self.run_entry([SEMANTIC, FORM])
        self.assertEqual(rc, 0)
        self.assertEqual(len(taps), 1)

    def test_no_coordinates_never_tap(self):
        with patch.object(entry, "method_coords", return_value=None), \
             patch.object(entry, "email_entry", return_value=None):
            rc, log, taps, _, _ = self.run_entry([CHOOSER])
        self.assertEqual(rc, 3)
        self.assertIn("METHOD_NOT_FOUND", log)
        self.assertEqual(taps, [])

    def test_phone_method_chooses_phone_segment(self):
        rc, log, taps, _, _ = self.run_entry([CHOOSER, FORM], "phone")
        self.assertEqual(rc, 0)
        self.assertIn("TAPPED=PHONE", log)
        self.assertEqual(len(taps), 1)

    def test_invalid_method_fails_closed(self):
        with patch.object(sys, "argv", ["entry.py", "sms"]), patch.object(entry, "snapshot") as snap:
            self.assertEqual(entry.main(), 2)
            snap.assert_not_called()

    def test_auto_email_for_address(self):
        rc, log, taps, _, _ = self.run_entry([CHOOSER, FORM], "auto", {"KWAI_LOGIN": "test@example.invalid", "KWAI_LOGIN_METHOD": ""})
        self.assertEqual(rc, 0)
        self.assertIn("TAPPED=EMAIL", log)

    def test_auto_phone_for_digits(self):
        rc, log, taps, _, _ = self.run_entry([CHOOSER, FORM], "auto", {"KWAI_LOGIN": "5511999999999", "KWAI_LOGIN_METHOD": ""})
        self.assertEqual(rc, 0)
        self.assertIn("TAPPED=PHONE", log)

    def test_auto_forced_email_over_phone(self):
        rc, log, taps, _, _ = self.run_entry([CHOOSER, FORM], "auto", {"KWAI_LOGIN": "5511999999999", "KWAI_LOGIN_METHOD": "email"})
        self.assertEqual(rc, 0)
        self.assertIn("TAPPED=EMAIL", log)

    def test_adb_timeout_returns_ui_unavailable(self):
        with patch.object(entry, "snapshot", side_effect=subprocess.TimeoutExpired("adb", 12)), \
             patch.object(sys, "argv", ["entry.py", "email"]), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(entry.main(), 2)
            self.assertIn("UI_UNAVAILABLE", output.getvalue())

    def test_bad_xml_returns_ui_unavailable(self):
        with patch.object(entry, "snapshot", side_effect=ET.ParseError("invalid")), \
             patch.object(sys, "argv", ["entry.py", "email"]):
            self.assertEqual(entry.main(), 2)

    def test_snapshot_returns_xml_for_semantic_locator(self):
        with patch.object(entry, "adb", side_effect=[b"", CHOOSER.encode("utf-8")]) as adb:
            nodes, xml = entry.snapshot()
        self.assertEqual(xml, CHOOSER)
        self.assertTrue(native_chooser_visible(nodes, xml))
        self.assertEqual(adb.call_count, 2)

    def test_snapshot_unicode_decoding(self):
        xml = "<hierarchy><node text='Entrar' bounds='[0,0][10,10]'/></hierarchy>"
        with patch.object(entry, "adb", side_effect=[b"", xml.encode("utf-8")]):
            nodes, value = entry.snapshot()
        self.assertIn("Entrar", value)
        self.assertEqual(len(nodes), 1)

    def test_search_field_is_not_login_form(self):
        self.assertFalse(email_form_visible(snapshot(SEARCH)[0]))

    def test_no_tap_on_empty_chooser(self):
        self.assertFalse(native_chooser_visible(snapshot(EMPTY)[0], EMPTY))
        self.assertIsNone(email_entry(snapshot(EMPTY)[0], EMPTY))

    def test_log_does_not_expose_login_identifier(self):
        rc, log, _, _, _ = self.run_entry([CHOOSER, FORM], "auto", {"KWAI_LOGIN": "private@example.invalid", "KWAI_LOGIN_METHOD": ""})
        self.assertEqual(rc, 0)
        self.assertNotIn("private@example.invalid", log)

if __name__ == "__main__":
    unittest.main(verbosity=2)
