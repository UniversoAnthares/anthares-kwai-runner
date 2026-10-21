import unittest
from unittest.mock import patch
from tools import cortes_linkedin_neon_fanout as worker

def state(n):
    return {"items":[{"video_id":"live1","title":"Texto de apresentação","clips":[{
       "type":"short","stored":True,"segment_id":f"live1:{i*1000}:{i*1000+55000}",
       "attachment_id":i+1,"duration_seconds":55,
       "url":f"https://anthares.us/wp-content/uploads/{i}.mp4"} for i in range(n)]}]}


class CloudLinkedinFanoutTests(unittest.TestCase):
    def test_reserves_first_20_linkedin_jobs_from_100_valid_masters(self):
        jobs=worker.candidate_jobs(state(100))
        self.assertEqual(len(jobs),20)
        self.assertEqual({x["platform"] for x in jobs},{"linkedin"})
        self.assertEqual({x["target_key"] for x in jobs},{"linkedin:primary"})
        self.assertEqual(len({x["id"] for x in jobs}),20)
        self.assertEqual([x["source_start"] for x in jobs],list(range(0,20000,1000)))

    def test_dedupe_idempotent_and_hash_matches(self):
        a=worker.candidate_jobs(state(1))[0]
        b=worker.candidate_jobs(state(1))[0]
        self.assertEqual(a,b)
        self.assertEqual(a["id"],a["dedupe_key"])

    def test_invalid_masters_not_queued(self):
        s=state(2)
        s["items"][0]["clips"][0]["duration_seconds"]=91
        s["items"][0]["clips"][1]["url"]="https://anthares.us.attacker.test/clip.mp4"
        self.assertEqual(worker.candidate_jobs(s),[])

    def test_fails_closed_on_local_execution(self):
        with patch.dict(worker.os.environ,{"GITHUB_ACTIONS":"false","RUNNER_OS":"Windows"},clear=True):
            with self.assertRaisesRegex(RuntimeError,"MUST_RUN_IN_CLOUD"):
                worker.require_cloud()

    def test_conflicting_master_url_is_blocked(self):
        s=state(1)
        s["items"][0]["clips"].append({**s["items"][0]["clips"][0],"url":"https://anthares.us/another.mp4"})
        with self.assertRaisesRegex(RuntimeError,"COLLISION"):
            worker.candidate_jobs(s)


if __name__=="__main__":
    unittest.main()
