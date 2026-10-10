#!/usr/bin/env python3
"""Offline regression: UI chooser must not be mistaken for credential fields."""
import unittest
from kwai_login_ui_state import classify


class KwaiLoginUiStateTests(unittest.TestCase):
    def test_actual_diagnostic_chooser_labels(self):
        xml = """<hierarchy><node class="android.view.ViewGroup">
        <node class="android.widget.TextView" text="Create your profile"/>
        <node class="android.widget.TextView" resource-id="com.kwai.video:id/login_platform_item_text"
              text="Continue with Google"/>
        <node class="android.widget.TextView" resource-id="com.kwai.video:id/login_platform_expand_text"
              text="or use Facebook  |  Phone  |  Email"/>
        </node></hierarchy>"""
        self.assertEqual(classify(xml), "CHOOSER")

    def test_email_form(self):
        xml = """<hierarchy><node class="android.widget.TextView" text="Email"/>
        <node class="android.widget.EditText" resource-id="com.kwai.video:id/email"/>
        <node class="android.widget.EditText" resource-id="com.kwai.video:id/password"/>
        </hierarchy>"""
        self.assertEqual(classify(xml), "CREDENTIAL_FORM")

    def test_feed_with_email_text_is_not_form(self):
        xml = """<hierarchy><node class="android.widget.TextView"
        text="Share video by email"/></hierarchy>"""
        self.assertEqual(classify(xml), "UNKNOWN")

    def test_bad_xml(self):
        self.assertEqual(classify("<hierarchy>"), "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
