"""Kwai caption bridge remains reversible and fails closed before publication."""
from __future__ import annotations
import base64
import importlib.util
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("kwai_core_uiautomator_caption_test", ROOT / "kwai-up" / "kwai_up.py")
kwai = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = kwai
spec.loader.exec_module(kwai)


class FakeADB:
    def __init__(self, output: str):
        self.output = output
        self.calls: list[tuple[str, ...]] = []

    def run(self, *args: str, **kwargs):
        self.calls.append(args)
        if len(args) >= 3 and args[:3] == ("shell", "uiautomator", "runtest"):
            return self.output
        return "1 file pushed"


def test_publisher(text: str, output: str):
    publisher = object.__new__(kwai.Publisher)
    publisher.cfg = SimpleNamespace(caption=text)
    publisher.adb = FakeADB(output)
    publisher.tap_node = lambda *args, **kwargs: None
    return publisher


class UnicodeCaptionTests(unittest.TestCase):
    def test_writes_original_utf8_exactly_and_requires_instrumentation_success(self):
        with TemporaryDirectory() as tmp:
            jar = Path(tmp) / "driver.jar"
            jar.write_bytes(b"test-only-sentinel")
            text = "A Poética de Aristóteles — Parte 1 (LIVE) #Literatura"
            pub = test_publisher(text, "ANTHARES_UI_OK action=setFirstEditText\nOK (1 test)")
            with patch.dict(os.environ, {"KWAI_UP_UIAUTOMATOR_JAR": str(jar)}), patch.object(kwai.time, "sleep"):
                pub.fill_caption([{"resource-id": kwai.EDITOR_ID}])
            calls = pub.adb.calls
            self.assertEqual(calls[0][:2], ("push", str(jar)))
            instrument = next(x for x in calls if x[:3] == ("shell", "uiautomator", "runtest"))
            self.assertIn("setFirstEditText", instrument)
            self.assertEqual(base64.b64decode(instrument[-1]).decode("utf-8"), text)
            self.assertNotIn(("shell", "input", "text"), [x[:3] for x in calls])
            self.assertNotIn("post", str(calls).lower())

    def test_error_without_success_proof_prevents_publish(self):
        with TemporaryDirectory() as tmp:
            jar = Path(tmp) / "driver.jar"
            jar.write_bytes(b"test-only-sentinel")
            pub = test_publisher("A Poética de Aristóteles", "Tests run: 1, Errors: 1")
            with patch.dict(os.environ, {"KWAI_UP_UIAUTOMATOR_JAR": str(jar)}):
                with self.assertRaisesRegex(kwai.KwaiUpError, "caption-uiautomator-set-text-failed"):
                    pub.fill_caption([{"resource-id": kwai.EDITOR_ID}])
            self.assertFalse(any("post" in str(call).lower() for call in pub.adb.calls))

    def test_missing_driver_fails_closed(self):
        pub = test_publisher("Legenda", "OK (1 test)")
        with patch.dict(os.environ, {"KWAI_UP_UIAUTOMATOR_JAR": "/nonexistent/anthares-ui-driver.jar"}):
            with self.assertRaisesRegex(kwai.KwaiUpError, "caption-uiautomator-jar-missing"):
                pub.fill_caption([{"resource-id": kwai.EDITOR_ID}])


if __name__ == "__main__":
    unittest.main()
