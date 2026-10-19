"""Current Kwai profile selector and read-only confirmation retry contract."""
from __future__ import annotations
import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("kwai_current_profile_core",ROOT/"kwai-up"/"kwai_up.py")
core=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=core
spec.loader.exec_module(core)
sys.path.insert(0,str(ROOT/"tools"))
import kwai_memu_queue_safe as memu


class ProfileNavigationTests(unittest.TestCase):
    def test_prefers_verified_bottom_profile_label_to_legacy_profile_control(self):
        publisher=object.__new__(core.Publisher)
        legacy={"resource-id":core.PROFILE_TAB_IDS[0],"text":"other","bounds":"[0,0][90,90]"}
        current={"resource-id":"com.kwai.video.basis:id/consume_tab_text",
                 "text":"Perfil","bounds":"[600,1190][695,1280]"}
        self.assertIs(publisher.profile_tab([legacy,current]),current)

    def test_no_generic_profile_text_click_without_exact_resource_id(self):
        publisher=object.__new__(core.Publisher)
        text_only={"resource-id":"com.kwai.video.basis:id/tv_slide_play_user_name",
                   "text":"Perfil","bounds":"[60,200][400,400]"}
        self.assertIsNone(publisher.profile_tab([text_only]))

    def test_verifier_retries_transient_identity_failure(self):
        publisher=object.__new__(memu.QueuePublisher)
        publisher.cfg=SimpleNamespace(verify_timeout=10)
        publisher.verify_identity=lambda: None
        publisher.profile_fingerprints=lambda *a,**kw: ["new","old-1","old-2"]
        with patch.object(publisher,"verify_identity",side_effect=[memu.ku.KwaiUpError("navigation-unavailable"),None]) as identity, \
             patch.object(memu.ku,"profile_grid_changed",return_value=True), \
             patch.object(memu.time,"sleep"):
            ok,proof=publisher.verify_after_post(["old-1","old-2","old-3"])
        self.assertTrue(ok)
        self.assertEqual(identity.call_count,2)
        self.assertIn("new-profile-card",proof)

    def test_human_verification_aborts_read_only_retry(self):
        publisher=object.__new__(memu.QueuePublisher)
        publisher.cfg=SimpleNamespace(verify_timeout=10)
        publisher.verify_identity=lambda: (_ for _ in ()).throw(memu.ku.HumanVerification("human-verification"))
        with self.assertRaises(memu.ku.HumanVerification):
            publisher.verify_after_post(["old-1"])


if __name__=="__main__":
    unittest.main()
