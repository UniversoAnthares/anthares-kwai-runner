from __future__ import annotations

import importlib.util
import pathlib
import struct
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ENTRY = ROOT / "kwai_up_physical_entry.py"
SPEC = importlib.util.spec_from_file_location("kwai_up_physical_entry_test", ENTRY)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class PhysicalContractTests(unittest.TestCase):
    def test_zero_area_nodes_are_invisible(self):
        self.assertIsNone(mod._visible_bounds({"bounds": "[0,0][0,0]"}))
        self.assertIsNone(mod._visible_center("[0,0][0,0]"))

    def test_visible_node_center(self):
        self.assertEqual(mod._visible_bounds({"bounds": "[0,354][360,715]"}), (0, 354, 360, 715))
        self.assertEqual(mod._visible_center("[0,354][360,715]"), (180, 534))

    def test_lite_resource_contract(self):
        ku = mod.ku
        self.assertEqual(ku.PACKAGE, "kwai.lite.video")
        self.assertEqual(ku.PREVIEW_CONTAINER_ID, "kwai.lite.video.basis:id/preview_container")
        self.assertEqual(ku.NEXT_ID, "kwai.lite.video.product:id/edit_post_next_step_button")
        self.assertEqual(ku.FINAL_POST_ID, "kwai.lite.video.basis:id/post")
        self.assertEqual(ku.EDITOR_ID, "kwai.lite.video.basis:id/editor")
        self.assertEqual(ku.PRIVACY_ID, "kwai.lite.video.product:id/tv_select_permission")

    def test_uhid_touch_encodes_target_not_origin(self):
        event = mod.ps._input_event(True, 180, 534, 1080, 2340)
        event_type, size, flags, x, y = struct.unpack("<IHBHH", event)
        self.assertEqual(event_type, 12)
        self.assertEqual(size, 5)
        self.assertEqual(flags, 3)
        self.assertGreater(x, 0)
        self.assertGreater(y, 0)
        self.assertEqual(x, round(180 * 32767 / 1080))
        self.assertEqual(y, round(534 * 32767 / 2340))

    def test_uhid_release_clears_tip_switch(self):
        event = mod.ps._input_event(False, 180, 534, 1080, 2340)
        _, size, flags, _, _ = struct.unpack("<IHBHH", event)
        self.assertEqual(size, 5)
        self.assertEqual(flags, 0)

    def test_prepare_and_commit_remain_separate(self):
        source = (ROOT / "kwai_up.py").read_text(encoding="utf-8")
        prepare_body = source.split("    def prepare(self) -> int:", 1)[1].split("    def load_ready", 1)[0]
        commit_body = source.split("    def commit(self) -> int:", 1)[1].split("    def verify", 1)[0]
        self.assertNotIn('self.tap_node(post', prepare_body)
        self.assertIn('self.tap_node(post', commit_body)

    def test_physical_navigation_targets_deep_link_and_scroll_path(self):
        source = ENTRY.read_text(encoding="utf-8")
        self.assertIn('"kwai://album"', source)
        self.assertIn('"album_scroll_to_path"', source)
        self.assertIn('PHYSICAL_TARGET', source)
        self.assertIn('PHYSICAL_NEXT', source)


if __name__ == "__main__":
    unittest.main()
