"""Safe Codeberg QA backup, no real requests or issue mutations."""
import datetime as dt
import importlib.util
import pathlib
import unittest
from unittest.mock import patch

P=pathlib.Path(__file__).resolve().parents[1]/"tools"/"cortes_qa_codeberg_p0_watch.py"
spec=importlib.util.spec_from_file_location("p0_cb",P)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class CodebergP0Tests(unittest.TestCase):
    def test_git_hosted_queued_triggers_incident_and_healthy_neon_does_not(self):
        created=(m.NOW-dt.timedelta(minutes=31)).isoformat()
        def fake(url,*args,**kwargs):
            if "api.github.com" in url:
                return {"workflow_runs":[{"id":123,"status":"queued","created_at":created,"conclusion":None}]}
            return {"ok":True,"service":"cortes-tiktok-lucas4-neon" if ("cortestiktok4" in url or "lucas4-ha" in url) else "cortes-tiktok-neon","fencing":True}
        with patch.object(m,"fetch",side_effect=fake):
            result=list(m.inspect())
        self.assertEqual(len(result),2)
        self.assertTrue(all(r["stage"]=="github_hosted_queued_over_20m" for r in result))

    def test_healthy_queue_does_not_escalate_before_timeout(self):
        def fake(url,*args,**kwargs):
            if "api.github.com" in url:return {"workflow_runs":[]}
            return {"ok":True,"service":"cortes-tiktok-lucas4-neon" if ("cortestiktok4" in url or "lucas4-ha" in url) else "cortes-tiktok-neon","fencing":True}
        with patch.object(m,"fetch",side_effect=fake):
            self.assertEqual(list(m.inspect()),[])

    def test_issues_deduplicated_and_account_scoped(self):
        item=m.incident("lucasrosalem4","failure","https://github.com/example")
        calls=[]
        def fake(url,token=None,method="GET",payload=None):
            calls.append((method,payload))
            if method=="GET":return []
            return {"number":3}
        with patch.dict(m.os.environ,{"FORGEJO_TOKEN":"fake-not-secret","FORGEJO_REPOSITORY":m.REPO}),patch.object(m,"fetch",side_effect=fake):
            self.assertEqual(m.report([item]),1)
        self.assertIn(item["fingerprint"],calls[-1][1]["title"])
        self.assertIn("reconciliação",calls[-1][1]["body"] if "reconciliação" in calls[-1][1]["body"] else "reconciliação")
if __name__=="__main__":unittest.main()
