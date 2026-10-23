"""Offline contracts: free TinyFetch first, safe fallback, no false publication."""
import importlib.util
import io
import json
import os
import pathlib
import unittest
from unittest import mock

FILE = pathlib.Path(__file__).resolve().parents[1] / "tools" / "tinyfish_public_probe.py"
spec = importlib.util.spec_from_file_location("tinyfish_public_probe", FILE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class Response:
    def __init__(self, payload, url="https://www.kwai.com/@lucasrosalem"):
        self.payload = payload
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, n):
        return self.payload[:n]

    def geturl(self):
        return self.url


class PublicReadContract(unittest.TestCase):
    def test_reject_nonpublic_and_unsafe_urls(self):
        for url in ("http://example.com", "https://localhost/a",
                    "https://127.0.0.1/a", "https://user:pass@example.com/",
                    "file:///etc/passwd", "https://test.local/"):
            with self.assertRaises(ValueError, msg=url):
                probe.probe_public_page(url)

    @mock.patch.dict(os.environ, {"TINYFISH_API_KEY": ""})
    def test_missing_key_does_not_block_platform_verifier(self):
        with mock.patch.object(probe.urllib.request, "urlopen") as call:
            report = probe.probe_public_page("https://www.kwai.com/@lucasrosalem")
            self.assertFalse(report["ok"])
            self.assertEqual(report["reason"], "tinyfish_key_unconfigured")
            call.assert_not_called()

    @mock.patch.dict(os.environ, {"TINYFISH_API_KEY": "test-placeholder"})
    def test_tinyfish_primary_and_marker_read(self):
        doc = {"results": [{"final_url": "https://www.kwai.com/@lucasrosalem",
                            "text": "<html><body>Lucas Rosalem publicou uma live especial sobre Lovecraft e poesia brasileira.</body></html>"}],
               "errors": []}
        with mock.patch.object(probe.urllib.request, "urlopen",
                               return_value=Response(json.dumps(doc).encode())) as call:
            report = probe.probe_public_page("https://www.kwai.com/@lucasrosalem",
                                             ("Lucas Rosalem",))
        self.assertTrue(report["ok"])
        self.assertEqual(report["provider"], "tinyfish_fetch")
        self.assertTrue(report["markers_matched"]["Lucas Rosalem"])
        self.assertEqual(call.call_count, 1)
        self.assertNotIn("test-placeholder", json.dumps(report))

    @mock.patch.dict(os.environ, {"TINYFISH_API_KEY": "test-placeholder"})
    def test_no_false_success_when_results_empty(self):
        payload = json.dumps({"results": [], "errors": [{"code": "bot_blocked"}]}).encode()
        with mock.patch.object(probe.urllib.request, "urlopen",
                               return_value=Response(payload)):
            report = probe.probe_public_page("https://www.kwai.com/@lucasrosalem")
        self.assertFalse(report["ok"])
        self.assertEqual(report["reason"], "tinyfish_empty_or_source_failed")

    @mock.patch.dict(os.environ, {"TINYFISH_API_KEY": "test-placeholder"})
    def test_fallback_after_provider_failure(self):
        bad = Response(json.dumps({"results": [], "errors": [{"code": "timeout"}]}).encode())
        good = Response(b"<html>Lucas Rosalem publica videos verificados nesta plataforma</html>")
        with mock.patch.object(probe.urllib.request, "urlopen", side_effect=[bad, good]) as call:
            report = probe.probe_public_page("https://www.kwai.com/@lucasrosalem", fallback=True)
        self.assertTrue(report["ok"])
        self.assertEqual(report["provider"], "https_fallback")
        self.assertEqual(call.call_count, 2)

    @mock.patch.dict(os.environ, {"TINYFISH_API_KEY": "test-placeholder"})
    def test_allowlisted_short_link_redirects_and_redacts_query(self):
        url = "https://k.kwai.com/p/ABC123?tracking=private-marker"
        doc = {"results": [{"final_url": "https://www.kwai.com/@lucasrosalem/photo/123",
                            "text": "<html>Lucas Rosalem shared a public video and an overview of this video on the profile.</html>"}],
               "errors": []}
        with mock.patch.object(probe.urllib.request, "urlopen",
                               return_value=Response(json.dumps(doc).encode())):
            report = probe.probe_public_page(url, allowed_hosts=("k.kwai.com", "www.kwai.com"))
        self.assertTrue(report["ok"])
        self.assertEqual(report["url"], "https://k.kwai.com/p/ABC123")
        self.assertNotIn("private-marker", json.dumps(report))

    @mock.patch.dict(os.environ, {"TINYFISH_API_KEY": "test-placeholder"})
    def test_reject_redirect_to_other_domain(self):
        doc = {"results": [{"final_url": "https://evil.example/posts/1",
                            "text": "A sufficiently long body of content so that a redirect must still be rejected."}],
               "errors": []}
        with mock.patch.object(probe.urllib.request, "urlopen",
                               return_value=Response(json.dumps(doc).encode())):
            report = probe.probe_public_page("https://k.kwai.com/p/ABC123",
                                            allowed_hosts=("k.kwai.com", "www.kwai.com"))
        self.assertFalse(report["ok"])
        self.assertEqual(report["reason"], "valueerror")


if __name__ == "__main__":
    unittest.main()
