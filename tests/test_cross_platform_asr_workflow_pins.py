"""All active hosted media publishers must use the tested Whisper/PyAV ABI."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
FILES=[
    ".github/workflows/instagram-auto-10day.yml",
    ".github/workflows/x-cloud-fullflow.yml",
    ".github/workflows/x-real-fullflow-once.yml",
    ".github/workflows/tiktok-real-publish.yml",
]

class TestASRDependencyABI(unittest.TestCase):
    def test_active_media_workflows_pin_compatible_versions(self):
        for name in FILES:
            with self.subTest(workflow=name):
                source=(ROOT/name).read_text(encoding="utf-8")
                self.assertIn("'faster-whisper==1.2.1'",source)
                self.assertIn("'av==17.1.0'",source)

    def test_each_runtime_has_preflight(self):
        for name in FILES:
            with self.subTest(workflow=name):
                source=(ROOT/name).read_text(encoding="utf-8")
                self.assertIn("av.__version__",source)

if __name__=="__main__":
    unittest.main()
