"""Regression coverage for ADB input text on the Kwai MEmu standby."""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import kwai_device_failover_worker as worker


class KwaiMemuCaptionTests(unittest.TestCase):
    def test_portuguese_title_transliterates_without_losing_words(self):
        result = worker.memu_caption_input("A Poética de Aristóteles - Parte 1 (LIVE)")
        self.assertEqual(result, "A Poetica de Aristoteles Parte 1 LIVE")
        self.assertTrue(result.isascii())

    def test_shell_control_characters_never_reach_adb(self):
        result = worker.memu_caption_input("Título & nota; `reboot` $(x) | mais")
        self.assertEqual(result, "Titulo nota reboot x mais")
        self.assertTrue(result.isascii())

    def test_fallback_if_no_typable_caption(self):
        self.assertEqual(worker.memu_caption_input("🌿🎞️"), "Universo Anthares")

    def test_core_injects_individual_words_and_real_space_keys(self):
        import importlib.util
        from types import SimpleNamespace
        from unittest.mock import patch
        core_path = Path(__file__).resolve().parents[1] / "kwai-up" / "kwai_up.py"
        spec = importlib.util.spec_from_file_location("kwai_up_caption_regression", core_path)
        core = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = core
        spec.loader.exec_module(core)
        publisher = object.__new__(core.Publisher)
        caption = worker.memu_caption_input("A Poética de Aristóteles - Parte 1 (LIVE)")
        publisher.cfg = SimpleNamespace(caption=caption)
        events = []
        class FakeADB:
            def run(self, *args, **kwargs):
                events.append(args)
                return ""
        publisher.adb = FakeADB()
        publisher.tap_node = lambda *args, **kwargs: None
        with patch.object(core.time, "sleep"):
            publisher.fill_caption([{"resource-id": core.EDITOR_ID}])
        tokens = caption.split()
        typed = [e[-1] for e in events if len(e) >= 3 and e[:3] == ("shell", "input", "text")]
        spaces = [e for e in events if e[-1] == "KEYCODE_SPACE"]
        self.assertEqual(typed, tokens)
        self.assertEqual(len(spaces), len(tokens)-1)

    def test_bound_length(self):
        self.assertLessEqual(len(worker.memu_caption_input("x"*300)), 120)


if __name__ == "__main__":
    unittest.main()
