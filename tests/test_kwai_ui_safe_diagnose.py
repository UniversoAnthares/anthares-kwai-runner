#!/usr/bin/env python3
"""Tests only synthetic UI trees; no login, network or account data."""
import importlib.util
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("kwai_ui_safe_diagnose",ROOT/"tools"/"kwai_ui_safe_diagnose.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def ui(*nodes):return "<hierarchy>"+"".join(nodes)+"</hierarchy>"
def node(text="",rid="",kind="android.widget.TextView"):
    return '<node class="%s" text="%s" resource-id="%s"/>'%(kind,text,rid)

class KwaiSafeDiagnosisTests(unittest.TestCase):
    def test_empty_tree_is_valid(self):
        self.assertEqual(mod.classify(ui())["node_count"],0)
    def test_onboarding_detection(self):
        self.assertTrue(mod.classify(ui(node("Choose like or dislike")))["interest_onboarding"])
    def test_login_chooser(self):
        self.assertTrue(mod.classify(ui(node("Email","com.kwai.video:id/login_platform_expand_text")))["login_chooser"])
    def test_resource_overlay(self):
        self.assertTrue(mod.classify(ui(node("Resource downloading 5%")))["resource_overlay"])
    def test_permission(self):
        self.assertTrue(mod.classify(ui(node("Don't allow","com.android.permissioncontroller:id/permission_deny_button")))["permission_modal"])
    def test_edittext_count(self):
        self.assertEqual(mod.classify(ui(node("","x","android.widget.EditText")))["edittext_count"],1)
    def test_no_raw_ui_in_output(self):
        raw=ui(node("Private Account User 123","com.kwai.video:id/other"))
        self.assertNotIn("Private",str(mod.classify(raw)))
        self.assertNotIn("123",str(mod.classify(raw)))
    def test_profile_tab(self):
        self.assertTrue(mod.classify(ui(node("","com.kwai.video:id/id_home_bottom_tab_me")))["profile_tab"])
    def test_alternate_profile_tab(self):
        state=mod.classify(ui(node("","com.kwai.video:id/ll_profile")))
        self.assertTrue(state["profile_tab"])
        self.assertTrue(state["main_navigation"])
    def test_profile_label_at_bottom(self):
        xml='<hierarchy><node class="android.view.View" bounds="[0,0][1080,2340]"/><node class="android.widget.TextView" text="Profile" bounds="[864,2123][1080,2274]"/></hierarchy>'
        self.assertTrue(mod.classify(xml)["profile_tab"])

    def test_profile_geometry_diagnostic(self):
        xml='<hierarchy><node class="android.view.View" bounds="[0,0][1080,2340]"/><node resource-id="com.kwai.video:id/profile_bottom" bounds="[864,2123][1080,2274]"/><node resource-id="com.kwai.video:id/profile_header" bounds="[70,50][700,150]"/><node resource-id="com.kwai.video:id/profile_hidden"/></hierarchy>'
        result=mod.classify(xml)
        self.assertEqual(result["profile_hint_bounded_count"],2)
        self.assertEqual(result["profile_hint_bottom_count"],1)
        self.assertEqual(result["profile_hint_unbounded_count"],1)
        self.assertNotIn("com.kwai.video:id/profile_bottom",str(result))

    def test_otp_challenge_without_private_code(self):
        state=mod.classify(ui(node("Enter verification code 123456")))
        self.assertTrue(state["verification_challenge"])
        self.assertNotIn("123456",str(state))
    def test_captcha_requires_human(self):
        self.assertTrue(mod.classify(ui(node("Slide to verify")))["captcha_challenge"])
    def test_phone_login_option(self):
        self.assertTrue(mod.classify(ui(node("Continue with phone")))["phone_login_option"])
    def test_google_login_option(self):
        self.assertTrue(mod.classify(ui(node("Continue with Google")))["google_login_option"])
    def test_email_login_option(self):
        self.assertTrue(mod.classify(ui(node("Continue with Email")))["email_login_option"])

    def test_system_error(self):
        self.assertTrue(mod.classify(ui(node("Kwai keeps stopping")))["system_error"])
    def test_no_false_form_from_email_label(self):
        self.assertFalse(mod.classify(ui(node("Email")))["login_form"])

if __name__=="__main__":unittest.main()
