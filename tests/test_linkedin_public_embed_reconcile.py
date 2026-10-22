"""Independent read-only LinkedIn public embed evidence contract."""
import unittest
import urllib.error
from unittest.mock import patch
from tools import cortes_linkedin_personal_cloud as p

class Response:
    def __init__(self,url,status=200): self.url,self.status=url,status
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def geturl(self): return self.url

class PublicProof(unittest.TestCase):
    def test_live_embed_200(self):
        x="urn:li:ugcPost:7518868047118413824"
        self.assertEqual(p.public_embed_status(x,opener=lambda req,timeout:Response(req.full_url)),200)
    def test_nonexistent_control_404(self):
        def missing(req,timeout):
            raise urllib.error.HTTPError(req.full_url,404,"missing",{},None)
        self.assertEqual(p.public_embed_status("urn:li:ugcPost:0000000000000000000",opener=missing),404)
    def test_login_redirect_not_proof(self):
        x="urn:li:ugcPost:7518868047118413824"
        self.assertEqual(p.public_embed_status(x,opener=lambda req,timeout:Response("https://www.linkedin.com/login")),0)
    def test_remote_invalid_fails_closed(self):
        self.assertEqual(p.public_embed_status("https://evil.invalid/",opener=lambda *args:None),0)
    def test_reconcile_only_when_control_missing_and_post_exists(self):
        calls=[]
        def queue(action,data):
            calls.append((action,data))
            if action=="pending":return {"ok":True,"jobs":[{"id":"cut-a","remote_id":"urn:li:ugcPost:7518868047118413824"}]}
            return {"ok":True}
        def status(remote):
            return 404 if remote==p._PUBLIC_EMBED_CONTROL else 200
        with patch.object(p,"cloud_only"),patch.object(p,"account_preflight"),patch.object(p,"queue",side_effect=queue),patch.object(p,"public_embed_status",side_effect=status):
            self.assertEqual(p.reconcile_personal(),1)
        self.assertEqual([c[0] for c in calls],["pending","reconcile-public"])
        self.assertEqual(calls[1][1]["control_status"],404)

if __name__=="__main__":unittest.main()
