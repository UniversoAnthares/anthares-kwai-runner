import io
import unittest
import urllib.error
from anthares_publisher.public_verify import verify,PublicVerificationError

class FakeResponse:
    status=200
    headers={"Content-Type":"text/html; charset=utf-8"}
    def __init__(self,url,body=b"<html><head><title>Post</title></head><body>OK</body></html>"):
        self.url=url
        self.body=body
    def __enter__(self):return self
    def __exit__(self,*a):return False
    def geturl(self):return self.url
    def read(self,n):return self.body[:n]

class FakeOpener:
    def __init__(self,final=None,err=None):
        self.final=final
        self.err=err
    def open(self,request,timeout=0):
        if self.err:raise self.err
        return FakeResponse(self.final or request.full_url)

class PublicVerifyTests(unittest.TestCase):
    def test_http_public_document_reachable(self):
        r=verify("https://www.kwai.com/v/video123","video123",opener=FakeOpener())
        self.assertTrue(r["http_public"])
        self.assertFalse(r["server_identity_verified"])
    def test_rejects_redirect_to_unrelated_post(self):
        with self.assertRaises(ValueError):
            verify("https://www.kwai.com/v/video123","video123",opener=FakeOpener("https://www.kwai.com/v/other"))
    def test_rejects_unavailable_public_page(self):
        with self.assertRaises(PublicVerificationError):
            verify("https://www.kwai.com/v/video123","video123",opener=FakeOpener(err=urllib.error.URLError("blocked")))
    def test_rejects_homepage_without_network(self):
        with self.assertRaises(ValueError):
            verify("https://www.kwai.com/","video123",opener=FakeOpener())

if __name__=="__main__":unittest.main()
