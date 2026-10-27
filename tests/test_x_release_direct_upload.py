"""Direct release reuse/upload tests. No disk writes or provider calls."""
import ast
import hashlib
import io
import json
from pathlib import Path
import re
import types
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/x_local_longform_producer.py"

def namespace(source):
    tree = ast.parse(source)
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                and n.name == "ensure_external_x_asset"]
    scope = {"hashlib": hashlib, "json": json, "re": re,
             "REPO": "UniversoAnthares/anthares-kwai-runner",
             "BASE": "repos/UniversoAnthares/anthares-kwai-runner"}
    exec(compile(ast.Module(body=selected, type_ignores=[]), "<release-helper>", "exec"), scope)
    return scope

class RenderedInput:
    payload = b"synthetic-approved-media"
    def stat(self):
        return types.SimpleNamespace(st_size=len(self.payload))
    def open(self, mode):
        assert mode == "rb"
        return io.BytesIO(self.payload)
    def __str__(self):
        return "existing-rendered-input.mp4"

class DirectReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
    def setUp(self):
        self.ns = namespace(self.source)
        self.file = RenderedInput()
        self.tag = "x-longform-auto-20261027"
        self.name = "anthares-x-abcdefghi12-600-0.mp4"
        self.info = {"width": 1280, "height": 720, "seconds": 600}
        self.url = ("https://github.com/UniversoAnthares/anthares-kwai-runner/"
                    "releases/download/" + self.tag + "/" + self.name)
        self.asset = {"name": self.name, "state": "uploaded",
                      "size": len(self.file.payload),
                      "digest": "sha256:" + hashlib.sha256(self.file.payload).hexdigest(),
                      "browser_download_url": self.url}
        self.release = {"id": 123, "tag_name": self.tag, "draft": False, "assets": [self.asset]}
        self.run = Mock()
        self.gh = Mock()
        self.ns.update(subprocess=types.SimpleNamespace(run=self.run, CREATE_NO_WINDOW=0),
                       gh=self.gh, preflight_video=Mock(return_value=self.info))
    def response(self, obj=None, code=0, error=""):
        return types.SimpleNamespace(returncode=code, stdout=json.dumps(obj), stderr=error)
    def invoke(self):
        return self.ns["ensure_external_x_asset"](self.file, self.tag, self.name, self.info)
    def test_existing_asset_reused_without_upload(self):
        self.run.return_value = self.response(self.release)
        self.assertEqual(self.invoke(), self.url)
        self.assertEqual(self.run.call_count, 1)
        self.gh.assert_not_called()
    def test_upload_uses_original_input_without_staging(self):
        self.release["assets"] = []
        self.run.side_effect = [self.response(self.release), self.response(self.asset)]
        self.assertEqual(self.invoke(), self.url)
        args = self.run.call_args.args[0]
        self.assertEqual(args[args.index("--input") + 1], str(self.file))
        self.assertIn("https://uploads.github.com/repos/UniversoAnthares/anthares-kwai-runner/releases/123/assets?name=" + self.name, args)
        self.assertNotIn("shutil.copy2(video, staging)", self.source)
    def test_digest_mismatch_denied(self):
        self.asset["digest"] = "sha256:" + "0" * 64
        self.run.return_value = self.response(self.release)
        with self.assertRaisesRegex(RuntimeError, "CONTENT_UNVERIFIED"):
            self.invoke()
        self.assertEqual(self.run.call_count, 1)
    def test_size_mismatch_denied(self):
        self.asset["size"] += 1
        self.run.return_value = self.response(self.release)
        with self.assertRaises(RuntimeError):
            self.invoke()
    def test_missing_digest_denied(self):
        del self.asset["digest"]
        self.run.return_value = self.response(self.release)
        with self.assertRaises(RuntimeError):
            self.invoke()
    def test_foreign_download_url_denied(self):
        self.asset["browser_download_url"] = "https://example.org/foreign.mp4"
        self.run.return_value = self.response(self.release)
        with self.assertRaises(RuntimeError):
            self.invoke()
    def test_duplicate_asset_names_denied(self):
        self.release["assets"].append(dict(self.asset))
        self.run.return_value = self.response(self.release)
        with self.assertRaisesRegex(RuntimeError, "AMBIGUOUS"):
            self.invoke()
    def test_auth_failure_does_not_create_release(self):
        self.run.return_value = self.response(code=1, error="gh: denied (HTTP 403)")
        with self.assertRaisesRegex(RuntimeError, "READ_FAILED"):
            self.invoke()
        self.gh.assert_not_called()
        self.assertEqual(self.run.call_count, 1)
    def test_quota_failure_does_not_retry_or_create(self):
        self.run.return_value = self.response(code=1, error="gh: rate limit (HTTP 429)")
        with self.assertRaises(RuntimeError):
            self.invoke()
        self.assertEqual(self.run.call_count, 1)
        self.gh.assert_not_called()
    def test_confirmed_404_allows_release_creation(self):
        empty = dict(self.release, assets=[])
        self.gh.return_value = empty
        self.run.side_effect = [self.response(code=1, error="gh: Not Found (HTTP 404)"),
                                self.response(self.asset)]
        self.assertEqual(self.invoke(), self.url)
        self.assertEqual(self.gh.call_args.args[0:2], ("/releases", "POST"))
    def test_ambiguous_upload_is_not_retried(self):
        self.release["assets"] = []
        self.run.side_effect = [self.response(self.release), self.response(code=1, error="connection lost")]
        with self.assertRaisesRegex(RuntimeError, "UPLOAD_UNCERTAIN"):
            self.invoke()
        self.assertEqual(self.run.call_count, 2)
    def test_uploaded_digest_must_match(self):
        self.release["assets"] = []
        self.asset["digest"] = "sha256:" + "f" * 64
        self.run.side_effect = [self.response(self.release), self.response(self.asset)]
        with self.assertRaises(RuntimeError):
            self.invoke()
    def test_media_changed_before_provider_read_is_rejected(self):
        self.ns["preflight_video"].return_value = {}
        with self.assertRaisesRegex(RuntimeError, "RENDERED_MEDIA_MISMATCH"):
            self.invoke()
        self.run.assert_not_called()
    def test_unapproved_destination_rejected_before_access(self):
        self.name = "../other.mp4"
        with self.assertRaisesRegex(RuntimeError, "DESTINATION_INVALID"):
            self.invoke()
        self.run.assert_not_called()
    def test_wrong_release_tag_is_rejected(self):
        self.release["tag_name"] = "other"
        self.run.return_value = self.response(self.release)
        with self.assertRaisesRegex(RuntimeError, "IDENTITY_UNVERIFIED"):
            self.invoke()
    def test_incomplete_asset_is_rejected(self):
        self.asset["state"] = "new"
        self.run.return_value = self.response(self.release)
        with self.assertRaises(RuntimeError):
            self.invoke()

if __name__ == "__main__":
    unittest.main()
