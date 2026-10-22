import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class XSourceWinGuardTests(unittest.TestCase):
    def test_all_ffmpeg_yt_dlp_subprocesses_are_hidden_on_windows(self):
        for filename in ("x_cloud_prepare.py", "x_cloud_render.py"):
            with self.subTest(filename=filename):
                tree=ast.parse((ROOT/filename).read_text(encoding="utf8"))
                all_runs=[n for n in ast.walk(tree)
                          if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
                          and isinstance(n.func.value,ast.Name)
                          and n.func.value.id=="subprocess" and n.func.attr=="run"]
                self.assertTrue(all_runs)
                for call in all_runs:
                    self.assertIn("creationflags",[kw.arg for kw in call.keywords],
                                  "subprocess would open a visible console at line "+str(call.lineno))

    def test_cached_scan_requires_exact_video_window_and_digest(self):
        prepare=(ROOT/"x_cloud_prepare.py").read_text(encoding="utf8")
        render=(ROOT/"x_cloud_render.py").read_text(encoding="utf8")
        for attr in ('"source_url"', '"scan_start"', '"scan_seconds"', '"sha256"'):
            self.assertIn(attr,prepare)
            self.assertIn(attr,render)
        self.assertIn("hashlib.file_digest",prepare)
        self.assertIn("hashlib.file_digest",render)
        self.assertIn("if not reuse:",render)
        self.assertIn("prep.download_scan(source_url,scan)",render)

    def test_cached_local_model_does_not_require_cloud_ai(self):
        source=(ROOT/"tools/x_local_longform_producer.py").read_text(encoding="utf8")
        self.assertIn('"X_WHISPER_MODEL": "small"',source)
        self.assertIn('"X_YT_COOKIE_FILE"',source)
        self.assertIn('MAX_OPEN = 2',source)
        self.assertNotIn("tinyfish.com",source.lower())


if __name__ == "__main__":
    unittest.main()
