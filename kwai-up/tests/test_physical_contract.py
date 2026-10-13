from __future__ import annotations

import importlib.util
import os
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
MODULE = ROOT / "kwai_up_physical.py"
SPEC = importlib.util.spec_from_file_location("kwai_up_physical_test", MODULE)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class PhysicalContractTests(unittest.TestCase):
    def test_lite_resource_contract(self):
        self.assertEqual(mod.PACKAGE, "kwai.lite.video")
        self.assertEqual(mod.PROFILE_TAB_ID, "kwai.lite.video.basis:id/id_home_bottom_tab_me")
        self.assertEqual(mod.PREVIEW_ID, "kwai.lite.video.basis:id/preview_container")
        self.assertEqual(mod.EDITOR_NEXT_ID, "kwai.lite.video.product:id/edit_post_next_step_button")
        self.assertEqual(mod.FINAL_POST_ID, "kwai.lite.video.basis:id/post")
        self.assertEqual(mod.EDITOR_ID, "kwai.lite.video.basis:id/editor")
        self.assertEqual(mod.PRIVACY_ID, "kwai.lite.video.product:id/tv_select_permission")

    def test_public_privacy_contract(self):
        self.assertIn("p\u00fablico", mod.PUBLIC_PRIVACY_VALUES)
        self.assertIn("publico", mod.PUBLIC_PRIVACY_VALUES)
        self.assertIn("public", mod.PUBLIC_PRIVACY_VALUES)
        self.assertNotIn("privado", mod.PUBLIC_PRIVACY_VALUES)

    def test_parse_nodes_keeps_focus_state(self):
        xml = b'<hierarchy><node text="x" resource-id="rid" class="x" package="p" clickable="true" enabled="true" selected="false" checked="false" bounds="[0,0][1,1]" focusable="true" focused="true" /></hierarchy>'
        node = mod.parse_nodes_full(xml)[0]
        self.assertEqual(node["focusable"], "true")
        self.assertEqual(node["focused"], "true")

    def test_choose_serial_keeps_requested_online(self):
        raw = "List of devices attached\nUSB123 device model:Phone\n192.168.1.35:5555 device model:Phone\n"
        self.assertEqual(mod.choose_serial(raw, "USB123"), "USB123")

    def test_choose_serial_recovers_stale_ip_to_physical_tcp(self):
        raw = "List of devices attached\nUSB123 device model:Phone\n127.0.0.1:21503 device model:Emu\n192.168.1.35:5555 device model:Phone\n"
        self.assertEqual(mod.choose_serial(raw, "192.168.1.2:5555"), "192.168.1.35:5555")

    def test_choose_serial_ignores_loopback_emulator(self):
        raw = "List of devices attached\n127.0.0.1:21503 device model:Emu\n192.168.1.35:5555 device model:Phone\n"
        self.assertEqual(mod.choose_serial(raw, ""), "192.168.1.35:5555")

    def test_choose_serial_refuses_two_physical_tcp_candidates(self):
        raw = "List of devices attached\n192.168.1.35:5555 device model:A\n192.168.1.36:5555 device model:B\n"
        with self.assertRaises(mod.ku.KwaiUpError):
            mod.choose_serial(raw, "")

    def test_case_specific_transport_variation(self):
        case = int(os.getenv("KWAI_UP_CASE", "1"))
        octet = 20 + (case % 200)
        physical = f"10.77.1.{octet}:5555"
        stale = f"10.66.1.{octet}:5555"
        loop_port = 21000 + case
        raw = (
            "List of devices attached\n"
            f"USB{case:02d} device model:Phone\n"
            f"127.0.0.1:{loop_port} device model:Emu\n"
            f"{physical} device model:Phone\n"
            f"10.77.2.{octet}:5555 offline model:Old\n"
        )
        self.assertEqual(mod.choose_serial(raw, stale), physical)

    def test_hid_ascii_mapping(self):
        self.assertEqual(mod.HIDKeyboard._ascii_key("a"), (0x04, 0))
        self.assertEqual(mod.HIDKeyboard._ascii_key("A"), (0x04, mod.SHIFT))
        self.assertEqual(mod.HIDKeyboard._ascii_key("@"), (0x1F, mod.SHIFT))
        self.assertEqual(mod.HIDKeyboard._ascii_key("#"), (0x20, mod.SHIFT))

    def test_hid_rejects_unmapped_unicode(self):
        with self.assertRaises(mod.ku.KwaiUpError):
            mod.HIDKeyboard._ascii_key("\u00e1")

    def test_prepare_uses_verified_focus_hints(self):
        source = MODULE.read_text(encoding="utf-8")
        self.assertIn("hint_steps=7", source)
        self.assertIn("hint_steps=10", source)
        self.assertIn("self.focused_target(nodes, rid)", source)

    def test_prepare_stops_at_ready_boundary(self):
        source = MODULE.read_text(encoding="utf-8")
        prepare_body = source.split("    def prepare(self) -> int:", 1)[1].split("    def verify_after_post_physical", 1)[0]
        self.assertIn("READY_TO_PUBLISH", prepare_body)
        self.assertNotIn("PUBLISH_REQUESTED", prepare_body)

    def test_commit_requires_exact_post_focus_before_enter(self):
        source = MODULE.read_text(encoding="utf-8")
        commit_body = source.split("    def commit(self) -> int:", 1)[1].split("    def verify(self) -> int:", 1)[0]
        self.assertIn("trusted_focused_final_post(nodes)", commit_body)
        self.assertIn("hid-focus-target-timeout:trusted-final-post", commit_body)
        self.assertIn("PUBLISH_REQUESTED", commit_body)
        self.assertIn("keyboard.enter()", commit_body)
        self.assertLess(commit_body.index("trusted_focused_final_post(nodes)"), commit_body.index("keyboard.enter()"))

    def test_final_and_ready_both_use_dynamic_native_post_lookup(self):
        source = MODULE.read_text(encoding="utf-8")
        navigate = source.split("    def navigate_to_final(", 1)[1].split("    def fill_caption(", 1)[0]
        prepare = source.split("    def prepare(self) -> int:", 1)[1].split("    def verify_after_post_physical", 1)[0]
        self.assertIn("post = find_final_post(final)", navigate)
        self.assertIn("post = find_final_post(final)", prepare)
        self.assertNotIn("post = ku.find_id(final, FINAL_POST_ID)", navigate)
        self.assertNotIn("post = ku.find_id(final, FINAL_POST_ID)", prepare)

    def test_commit_is_at_most_once_before_hid_enter(self):
        source = MODULE.read_text(encoding="utf-8")
        commit = source.split("    def commit(self) -> int:", 1)[1].split("    def verify(self) -> int:", 1)[0]
        self.assertIn("os.O_EXCL", commit)
        self.assertIn("os.fsync(fd)", commit)
        self.assertIn("publish-attempt-already-recorded:verify-only", commit)
        self.assertIn("publish_attempt_", commit)
        self.assertIn('"publish_attempt_" + str(proof["media_sha256"]) + ".json"', commit)
        self.assertNotIn('"publish_attempt_" + ku.safe_token(self.cfg.job_id)', commit)
        self.assertLess(commit.index("os.fsync(fd)"), commit.index('self.emit(\n                "PUBLISH_REQUESTED"'))
        self.assertLess(commit.index("os.fsync(fd)"), commit.index("keyboard.enter()"))
        self.assertNotIn("attempt.unlink(", commit)

    def test_native_post_requires_focused_enabled_clickable(self):
        rid = mod.FINAL_POST_ID
        valid = {"resource-id": rid, "focused": "true", "focusable": "true",
                 "clickable": "true", "enabled": "true"}
        self.assertEqual(mod.trusted_focused_final_post([valid]), valid)
        for field in ("focused", "focusable", "clickable", "enabled"):
            invalid = {**valid, field: "false"}
            self.assertIsNone(mod.trusted_focused_final_post([invalid]), field)

    def test_native_right_button_requires_exact_publish_label(self):
        rid = f"{mod.BASIS}/right_btn"
        valid = {"resource-id": rid, "text": "Publicar", "class": "android.widget.Button",
                 "focused": "true", "focusable": "true", "clickable": "true",
                 "enabled": "true"}
        self.assertEqual(mod.trusted_focused_final_post([valid]), valid)
        for label in ("Excluir", "Cancelar", "Privado", ""):
            self.assertIsNone(mod.trusted_focused_final_post([{**valid, "text": label}]))
        self.assertIsNone(mod.trusted_focused_final_post([{**valid, "class": "android.view.View"}]))

    def test_native_focus_rejects_untrusted_resource_id(self):
        fake = {"resource-id": f"{mod.BASIS}/other", "text": "Publicar",
                "class": "android.widget.Button", "focused": "true",
                "focusable": "true", "clickable": "true", "enabled": "true"}
        self.assertIsNone(mod.trusted_focused_final_post([fake]))

    def test_native_focus_prefers_exact_post_over_right_button(self):
        right = {"resource-id": f"{mod.BASIS}/right_btn", "text": "Publicar",
                 "class": "android.widget.Button", "focused": "true",
                 "focusable": "true", "clickable": "true", "enabled": "true"}
        post = {"resource-id": mod.FINAL_POST_ID, "focused": "true",
                "focusable": "true", "clickable": "true", "enabled": "true"}
        self.assertEqual(mod.trusted_focused_final_post([right, post]), post)

    def test_physical_job_routes_to_verified_adapter(self):
        source = (ROOT / "kwai_up_physical_job.py").read_text(encoding="utf-8")
        self.assertIn("kwai_up_physical.py", source)
        self.assertNotIn("kwai_up_physical_entry.py", source)


if __name__ == "__main__":
    unittest.main()