"""Read-only WP QA smoke tests without network or real credentials."""
import io
import json
import unittest
import urllib.error
from tools.cortes_wp_auth_smoke import probe, MAX_BYTES

class FakeResponse:
    status=200
    def __init__(self, payload): self.payload=payload
    def __enter__(self): return self
    def __exit__(self,*a): return False
    def read(self,limit): return self.payload

class WordPressSmokeTest(unittest.TestCase):
    def setUp(self):self.env={"WP_SITE_URL":"https://anthares.us","WP_USERNAME":"qa-limited","WP_APP_PASSWORD":"opaque secret"}
    def test_missing_credentials(self):
        self.assertEqual(probe({"WP_SITE_URL":"https://anthares.us"}),("AUTH_MISSING",2))
    def test_success_is_read_only_and_no_secret_print(self):
        def mock(req,timeout):
            self.assertEqual(req.get_method(),"GET")
            self.assertIn("Authorization",req.headers)
            self.assertNotIn("opaque secret",repr(req.headers))
            return FakeResponse(json.dumps({"items":[],"blocker":None}).encode())
        self.assertEqual(probe(self.env,mock),("AUTHENTICATED_JSON_ITEMS_0",0))
    def test_http_401_is_sanitized(self):
        def mock(req,timeout):
            raise urllib.error.HTTPError(req.full_url,401,"sensitive underlying provider response",{},None)
        self.assertEqual(probe(self.env,mock),("HTTP_401",2))
    def test_invalid_json(self):
        self.assertEqual(probe(self.env,lambda req,timeout:FakeResponse(b"not-json")),("INVALID_JSON",2))
    def test_invalid_structure_not_green(self):
        self.assertEqual(probe(self.env,lambda req,timeout:FakeResponse(b'{"other":true}')),("INVALID_SCHEMA",2))
    def test_valid_large_authenticated_response_within_qa_limit(self):
        data=json.dumps({"items":[{"description":"x"*2_100_000}],"blocker":None}).encode()
        self.assertLess(len(data), MAX_BYTES)
        self.assertEqual(probe(self.env,lambda req,timeout:FakeResponse(data)),("AUTHENTICATED_JSON_ITEMS_1",0))
    def test_response_above_qa_limit_fails_closed(self):
        self.assertEqual(probe(self.env,lambda req,timeout:FakeResponse(b"x"*(MAX_BYTES+1))),("PAYLOAD_TOO_LARGE",2))
    def test_invalid_http_site(self):
        env=dict(self.env,WP_SITE_URL="http://anthares.us")
        self.assertEqual(probe(env),("SITE_URL_INVALID",2))

if __name__ == "__main__": unittest.main()
