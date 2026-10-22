"""Offline regression for Pinterest QA ASR dependency failures and 24h-safe isolation."""
from pathlib import Path
from unittest import TestCase, mock
import builtins
import tempfile

from tools import cortes_pinterest_metadata_qa as worker

ROOT = Path(__file__).resolve().parents[1]
URL = "https://anthares.us/wp-content/uploads/anthares-clips/qa-mock-video.mp4"

class PinterestASRRecovery(TestCase):
    def test_missing_optional_asr_is_bounded_per_clip(self):
        original = builtins.__import__

        def simulate_missing(name, *args, **kwargs):
            if name == "faster_whisper":
                raise ModuleNotFoundError("test simulated missing wheel")
            return original(name, *args, **kwargs)

        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.object(worker, "CACHE", Path(folder)):
                with mock.patch("builtins.__import__", side_effect=simulate_missing):
                    with self.assertRaisesRegex(RuntimeError, "PINTEREST_ASR_ENGINE_MISSING"):
                        worker.transcript(URL)

    def test_ffmpeg_bundle_and_pinned_dependency_repair(self):
        source = (ROOT / "tools/cortes_pinterest_metadata_qa.py").read_text(encoding="utf8")
        launcher = (ROOT / "tools/run_pinterest_metadata_qa.ps1").read_text(encoding="utf8")
        self.assertIn("imageio_ffmpeg.get_ffmpeg_exe()", source)
        self.assertIn("ImportError,urllib.error.URLError", source)
        self.assertIn("faster-whisper==1.2.1", launcher)
        self.assertIn("imageio-ffmpeg==0.6.0", launcher)
        self.assertIn("$env:HF_HOME", launcher)
        self.assertIn("PINTEREST_QA_ASR_DEPENDENCIES_UNAVAILABLE", launcher)
