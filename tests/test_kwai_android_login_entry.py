#!/usr/bin/env python3
"""Synthetic regression for native Kwai login method selection; no Android secrets."""
import importlib.util
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
spec=importlib.util.spec_from_file_location("kwai_android_login_entry",ROOT/"tools"/"kwai_android_login_entry.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
CHOOSER="""<hierarchy><node class="android.widget.TextView" resource-id="com.kwai.video.basis:id/login_platform_expand_text" text="or use Facebook  |  Phone  |  Email" bounds="[265,1285][815,1376]" /></hierarchy>"""
FORM="""<hierarchy><node class="android.widget.EditText" resource-id="com.kwai.video:id/login_email_input" bounds="[50,250][1030,350]"/></hierarchy>"""
def parse(xml):return list(mod.ET.fromstring(xml).iter("node"))

class NativeMethodTests(unittest.TestCase):
    def test_email_rightmost_segment(self):
        x,y=mod.method_coords(parse(CHOOSER),"email")
        self.assertGreaterEqual(x,715)
        self.assertLessEqual(x,815)
        self.assertEqual(y,1330)
    def test_phone_middle_segment(self):
        x,y=mod.method_coords(parse(CHOOSER),"phone")
        self.assertGreater(x,450)
        self.assertLess(x,670)
        self.assertEqual(y,1330)
    def test_email_phone_not_same_coordinate(self):
        self.assertNotEqual(mod.method_coords(parse(CHOOSER),"phone"),mod.method_coords(parse(CHOOSER),"email"))
    def test_absent_chooser_is_not_tapped(self):
        self.assertIsNone(mod.method_coords(parse("<hierarchy/>"),"email"))
        self.assertIsNone(mod.method_coords(parse("<hierarchy/>"),"phone"))
    def test_existing_form_is_not_tapped(self):
        self.assertIsNone(mod.method_coords(parse(FORM),"email"))
        self.assertIsNone(mod.method_coords(parse(FORM),"phone"))
    def test_invalid_bounds_fail_closed(self):
        self.assertIsNone(mod.method_coords(parse(CHOOSER.replace("[265,1285][815,1376]","[815,1376][265,1285]")),"phone"))
    def test_autologin_uses_method_selector(self):
        s=(ROOT/"kwai_android_autologin.py").read_text()
        self.assertIn("tools/kwai_android_login_entry.py",s)
        self.assertNotIn('subprocess.run(["python3","kwai_phone_surface_probe.py"]',s)
        self.assertNotIn("KWAI_FILL_DEBUG_UI=",s)
    def test_method_regex_avoids_facebook(self):
        self.assertFalse(mod.METHODS["phone"].search("Facebook"))
        self.assertFalse(mod.METHODS["email"].search("Facebook"))

if __name__=="__main__":unittest.main()
