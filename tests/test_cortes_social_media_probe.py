import io
import unittest
import urllib.error

from tools.cortes_social_media_probe import available


class Response:
    status = 206
    headers = {"Content-Type": "video/mp4"}
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, length): return b"12345678"[:length]


class MediaProbeTests(unittest.TestCase):
    def test_exists(self):
        self.assertTrue(available("https://anthares.us/wp-content/uploads/anthares-clips/2026/10/a.mp4",
                                  opener=lambda req, timeout: Response()))
    def test_missing_never_uploads(self):
        def missing(req, timeout):
            raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, io.BytesIO(b""))
        self.assertFalse(available("https://anthares.us/a.mp4", opener=missing))
    def test_other_errors_not_misclassified_missing(self):
        def denied(req, timeout):
            raise urllib.error.HTTPError(req.full_url, 429, "Rate", {}, io.BytesIO(b""))
        with self.assertRaisesRegex(RuntimeError, "TEMPORARY"):
            available("https://anthares.us/a.mp4", opener=denied)
    def test_wrong_origin_rejected(self):
        with self.assertRaises(ValueError):
            available("https://evil.example/a.mp4", opener=lambda req,timeout: Response())


if __name__ == "__main__":
    unittest.main()
