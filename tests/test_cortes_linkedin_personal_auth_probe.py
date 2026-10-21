"""Secret-safe isolated checks for LinkedIn personal OAuth verification."""
import io
import json
import unittest
import urllib.error

from tools.cortes_linkedin_personal_auth_probe import verify, OAuthProbeFailed


class FakeHTTP:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit):
        return self.body[:limit]


class OAuthPersonalProbeTests(unittest.TestCase):
    def test_valid_userinfo(self):
        calls = []
        def opener(req, timeout):
            calls.append((req.get_method(), req.full_url, timeout,
                          req.get_header("Authorization")))
            return FakeHTTP(json.dumps({"sub":"AB-_123456", "name":"PRIVATE"}).encode())
        self.assertTrue(verify("sample-test-token-1234567890", opener=opener))
        self.assertEqual(calls[0][:3], ("GET", "https://api.linkedin.com/v2/userinfo", 20))
        self.assertEqual(calls[0][3], "Bearer sample-test-token-1234567890")

    def test_no_invalid_token(self):
        for value in ("", "secret\\nexfil", "x"):
            with self.subTest(value=value):
                with self.assertRaises(OAuthProbeFailed):
                    verify(value, opener=lambda *args, **kw: None)

    def test_no_member_id(self):
        for content in (b"{}", b'{"sub":"urn:li:organization:123"}',
                        b'{"sub":""}', b"invalid"):
            with self.subTest(content=content):
                with self.assertRaises(OAuthProbeFailed):
                    verify("sample-test-token-1234567890",
                           opener=lambda *args, **kw: FakeHTTP(content))

    def test_unauthorized_no_server_response_leak(self):
        def deny(*args, **kw):
            raise urllib.error.HTTPError("https://api.linkedin.com/v2/userinfo", 401,
                "PRIVATE_SECRET_MUST_NOT_APPEAR", {}, io.BytesIO(b"token=PRIVATE"))
        with self.assertRaisesRegex(OAuthProbeFailed, "TOKEN_NOT_AUTHORIZED"):
            verify("sample-test-token-1234567890", opener=deny)


if __name__ == "__main__":
    unittest.main()
