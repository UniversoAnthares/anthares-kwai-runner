#!/usr/bin/env python3
"""Offline regression: UI chooser must not be mistaken for credential fields."""
import unittest
from kwai_login_ui_state import classify, target_coordinates


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

    def test_expand_target_uses_xml_bounds(self):
        xml = """<hierarchy>
        <node class="android.widget.TextView" text="Create your profile"/>
        <node class="android.widget.TextView" text="Continue with Google"/>
        <node class="android.widget.TextView"
              resource-id="com.kwai.video:id/login_platform_expand_text"
              text="or use Facebook  |  Phone  |  Email"
              bounds="[100,1200][900,1300]"/>
        </hierarchy>"""
        self.assertEqual(target_coordinates(xml), ("EXPAND", 500, 1250))

    def test_email_is_preferred_after_expansion(self):
        xml = """<hierarchy>
        <node text="Continue with Google"/>
        <node text="Phone" bounds="[100,500][300,600]"/>
        <node text="Email" bounds="[500,500][900,600]"/>
        <node resource-id="login_platform_expand_text" text="Phone | Email"
              bounds="[100,700][900,800]"/>
        </hierarchy>"""
        self.assertEqual(target_coordinates(xml), ("EMAIL", 700, 550))

    def test_google_only_has_no_target(self):
        xml = """<hierarchy><node text="Create your profile"/>
        <node text="Continue with Google" bounds="[0,0][900,200]"/>
        </hierarchy>"""
        self.assertEqual(classify(xml), "CHOOSER")
        self.assertIsNone(target_coordinates(xml))

    def test_invalid_bounds_fail_closed(self):
        xml = """<hierarchy><node text="Continue with Google"/>
        <node resource-id="login_platform_expand_text"
              text="Phone | Email" bounds="[0,0][0,0]"/></hierarchy>"""
        self.assertIsNone(target_coordinates(xml))

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
