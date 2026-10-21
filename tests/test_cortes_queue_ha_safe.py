import json
import unittest
import urllib.error
from unittest.mock import patch

from tools import cortes_queue_ha as ha
from tools import cortes_buffer_three_fanout as fanout


class FakeReply:
    status=200
    def __init__(self,data):
        self.data=data
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self):return json.dumps(self.data).encode("utf-8")


class SafeFailover(unittest.TestCase):
    def setUp(self):
        self.token=lambda: "oidc_"+("A"*90)
        self.available=(ha.PROVIDERS[0],ha.PROVIDERS[1])

    def test_neon_is_used_when_vercel_health_fails(self):
        sent=[]
        def open_(request,timeout):
            sent.append(request.full_url)
            return FakeReply({"ok":True,"deduped":False,"job":{"id":"job-1"}})
        with patch.object(ha,"is_healthy",side_effect=lambda p:p==ha.PROVIDERS[1]):
            with patch.object(ha.urllib.request,"urlopen",side_effect=open_):
                r=ha.post("enqueue",{"id":"job-1"},self.token)
        self.assertTrue(r["ok"])
        self.assertEqual(len(sent),1)
        self.assertIn("cortesqueue.compute",sent[0])

    def test_instagram_explicit_neon_primary_before_vercel(self):
        requested=[]
        def request(request,timeout):
            requested.append(request.full_url)
            return FakeReply({"ok":True,"jobs":[]})
        with patch.dict(ha.os.environ,{"CORTES_QUEUE_PRIMARY":"neon",
                          "GITHUB_ACTIONS":"true","RUNNER_ENVIRONMENT":"github-hosted",
                          "RUNNER_OS":"Linux"}):
            with patch.object(ha,"is_healthy",return_value=True):
                with patch.object(ha.urllib.request,"urlopen",side_effect=request):
                    result=ha.post("buffer-pending",{},self.token)
        self.assertTrue(result["ok"])
        self.assertEqual(len(requested),1)
        self.assertIn("cortesqueue.compute",requested[0])

    def test_no_provider_hopping_on_401_even_with_explicit_primary(self):
        attempted=[]
        def deny(request,timeout):
            attempted.append(request.full_url)
            raise urllib.error.HTTPError(request.full_url,401,"denied",{},None)
        with patch.dict(ha.os.environ,{"CORTES_QUEUE_PRIMARY":"neon",
                          "GITHUB_ACTIONS":"true","RUNNER_ENVIRONMENT":"github-hosted",
                          "RUNNER_OS":"Linux"}):
            with patch.object(ha,"is_healthy",return_value=True):
                with patch.object(ha.urllib.request,"urlopen",side_effect=deny):
                    with self.assertRaisesRegex(ha.BackendUnavailable,"REJECTED_401"):
                        ha.post("buffer-pending",{},self.token)
        self.assertEqual(len(attempted),1)

    def test_never_retry_ambiguous_buffer_lease(self):
        attempted=[]
        def error(request,timeout):
            attempted.append(request.full_url)
            raise urllib.error.HTTPError(request.full_url,503,"Error",{},None)
        with patch.object(ha,"is_healthy",return_value=True):
            with patch.object(ha.urllib.request,"urlopen",side_effect=error):
                with self.assertRaisesRegex(ha.BackendUnavailable,"MUTATION_RESULT_UNCERTAIN"):
                    ha.post("buffer-lease",{"target_key":"linkedin:primary"},self.token)
        self.assertEqual(len(attempted),1)

    def test_enqueue_can_fail_over_using_one_stable_identity(self):
        seen=[]
        def open_(request,timeout):
            seen.append((request.full_url,request.data))
            if len(seen)==1:
                raise urllib.error.HTTPError(request.full_url,503,"Error",{},None)
            return FakeReply({"ok":True,"deduped":True,"reason":"identity","job":{"id":"id1"}})
        with patch.object(ha,"is_healthy",return_value=True):
            with patch.object(ha.urllib.request,"urlopen",side_effect=open_):
                out=ha.post("enqueue",{"id":"id1"},self.token)
        self.assertEqual(len(seen),2)
        self.assertEqual(seen[0][1],seen[1][1])
        self.assertTrue(out["deduped"])

    def test_429_cannot_be_bypassed_by_another_provider(self):
        attempts=[]
        def error(request,timeout):
            attempts.append(request.full_url)
            raise urllib.error.HTTPError(request.full_url,429,"Quota",{},None)
        with patch.object(ha,"is_healthy",return_value=True):
            with patch.object(ha.urllib.request,"urlopen",side_effect=error):
                with self.assertRaisesRegex(ha.BackendUnavailable,"REJECTED_429"):
                    ha.post("enqueue",{"id":"id1"},self.token)
        self.assertEqual(len(attempts),1)

    def test_no_auth_no_requests(self):
        with patch.object(ha.urllib.request,"urlopen",side_effect=AssertionError("NETWORK")):
            with self.assertRaisesRegex(ha.BackendUnavailable,"OIDC_UNAVAILABLE"):
                ha.post("enqueue",{"id":"x"},lambda:"")

    def test_failed_social_destination_does_not_block_other_destinations(self):
        example={"id":"cut-1","source_id":"live","segment_id":"live:0:55000",
                 "target_key":"linkedin:primary","media_url":"https://anthares.us/test.mp4"}
        seen=[]
        def emit(job):
            platform=job["platform"]
            seen.append(platform)
            if platform=="pinterest":
                raise RuntimeError("PINTEREST_RATE_LIMIT")
            return False
        with patch.object(fanout.linked,"require_cloud"):
            with patch.object(fanout.linked,"wp_state",return_value={}):
                with patch.object(fanout.linked,"candidate_jobs",return_value=[example]):
                    with patch.object(fanout,"enqueue",side_effect=emit):
                        with self.assertRaisesRegex(RuntimeError,"pinterest"):
                            fanout.main()
        self.assertEqual(seen,["instagram","pinterest","linkedin"])


if __name__=="__main__":
    unittest.main()
