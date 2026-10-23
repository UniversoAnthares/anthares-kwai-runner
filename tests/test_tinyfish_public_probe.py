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
    def test_allow_kwai_public_shortlink_redirect(self):
        short = "https://k.kwai.com/p/WCAQrpD2"
        destination = "https://www.kwai.com/@lucasrosalem/video/5213066680620194154?token=SECRET"
        doc = {"results":[{"final_url":destination,"text":"<html>Lucas Rosalem publicou um video e o perfil contem os cortes publicados com titulo correto.</html>"}],"errors":[]}
        with mock.patch.object(probe.urllib.request,"urlopen",return_value=Response(json.dumps(doc).encode())):
            result = probe.probe_public_page(short,("Lucas Rosalem",),allowed_hosts=("k.kwai.com","www.kwai.com"))
        self.assertTrue(result["ok"])
        self.assertEqual(result["provider"],"tinyfish_fetch")
        self.assertNotIn("SECRET",json.dumps(result))

    @mock.patch.dict(os.environ, {"TINYFISH_API_KEY": "test-placeholder"})
    def test_reject_public_redirect_outside_allowlist(self):
        short = "https://k.kwai.com/p/WCAQrpD2"
        doc = {"results":[{"final_url":"https://private.example.com/x","text":"<html>Lucas Rosalem publicou um video, com texto adequado e varias informacoes.</html>"}],"errors":[]}
        with mock.patch.object(probe.urllib.request,"urlopen",return_value=Response(json.dumps(doc).encode())):
            result = probe.probe_public_page(short,allowed_hosts=("k.kwai.com","www.kwai.com"))
        self.assertFalse(result["ok"])

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


if __name__ == "__main__":
    unittest.main()
