import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch, call

import requests
from tools import x_local_browser_consumer as local


def media_404(*args, **kwargs):
    raise requests.exceptions.HTTPError("not found",
                                        response=SimpleNamespace(status_code=404))


class XMediaQuarantineTests(unittest.TestCase):
    def issue(self, num):
        return ({"number":num,"title":"[X-PUBLISH] testing","state":"open"},
                {"platform":"x","account":"lucasyahn"})

    def test_404_isolated_and_next_video_attempted_in_same_run(self):
        seen=[]
        with patch.object(local,"cloud_owns_queue",return_value=False), \
             patch.object(local,"auth",return_value="token"), \
             patch.object(local,"listed",return_value=[self.issue(1),self.issue(2)]), \
             patch.object(local,"readstate",return_value={}), \
             patch.object(local,"one",side_effect=[media_404(),None]) as runner, \
             patch.object(local,"state",side_effect=lambda i,p,**kw:seen.append((i,p,kw))), \
             patch.object(local,"github",return_value={}):
            result=local.main()
        self.assertEqual(result,"ONE_ITEM_VISITED")
        self.assertEqual(runner.call_count,2)
        self.assertTrue(any(i==1 and p=="QUARANTINED_MEDIA" and kw["media_http"]==404
                            for i,p,kw in seen))

    def test_expired_404_discards_without_post_and_continues(self):
        started=(datetime.now(timezone.utc)-timedelta(hours=25)).isoformat()
        seen=[]; gh=[]
        previous={"phase":"QUARANTINED_MEDIA","quarantine_started":started}
        with patch.object(local,"cloud_owns_queue",return_value=False), \
             patch.object(local,"auth",return_value="token"), \
             patch.object(local,"listed",return_value=[self.issue(1),self.issue(2)]), \
             patch.object(local,"readstate",return_value=previous), \
             patch.object(local,"one",side_effect=[media_404(),None]) as runner, \
             patch.object(local,"state",side_effect=lambda n,p,**kw:seen.append((n,p))), \
             patch.object(local,"github",side_effect=lambda *args: gh.append(args) or {}):
            result=local.main()
        self.assertEqual(runner.call_count,2)
        self.assertEqual(result,"ONE_ITEM_VISITED")
        self.assertIn((1,"DISCARDED"),seen)
        self.assertTrue(any(args[0]=="/issues/1" and args[1]=="PATCH"
                            and args[2].get("state")=="closed" for args in gh))

    def test_cloud_uncertain_never_blind_retries_or_clears_fence(self):
        with patch.object(local,"cloud_owns_queue",return_value=False), \
             patch.object(local,"auth",return_value="token"), \
             patch.object(local,"listed",return_value=[self.issue(1),self.issue(2)]), \
             patch.object(local,"readstate",return_value={"phase":"SUBMISSION_STARTED"}), \
             patch.object(local,"one",side_effect=RuntimeError("UNCERTAIN")) as runner, \
             patch.object(local,"state") as state, \
             patch.object(local,"github",return_value={}):
            result=local.main()
        self.assertEqual(result,"UNCERTAIN_FENCED_NEXT_SCHEDULE")
        self.assertEqual(runner.call_count,1)
        self.assertEqual(state.call_args.args[:2],(1,"UNCERTAIN"))

if __name__=="__main__":
    unittest.main()
