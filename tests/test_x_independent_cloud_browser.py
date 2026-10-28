import ast
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from tools import x_local_browser_consumer as local
from tools import x_github_anthares_browser_publisher as cloud

ROOT=Path(__file__).resolve().parents[1]

class XIndependentCloudPrimaryTests(unittest.TestCase):
    def sample(self, **changes):
        row={"platform":"x","account":"lucasyahn","duration_class":"long",
             "media_url":"https://github.com/UniversoAnthares/anthares-kwai-runner/releases/download/x-longform-auto-20261022/proven.mp4",
             "caption":"Um trecho de literatura. #Literatura",
             "microedit":{"final_duration":520},
             "source_id":"source-1","segment_start":600,"segment_end":1120,
             "planned_at":(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat()}
        row.update(changes)
        fence=chr(96)*3
        return {"number":1,"state":"open","title":"[X-PUBLISH] source-1",
                "body":fence+"json\n"+json.dumps(row)+"\n"+fence}

    def test_cloud_accepts_only_exact_longform_video(self):
        self.assertIsNotNone(cloud.eligible(self.sample()))
        self.assertIsNone(cloud.eligible(self.sample(account="other")))
        self.assertIsNone(cloud.eligible(self.sample(duration_class="short")))
        self.assertIsNone(cloud.eligible(self.sample(media_url="https://evil.example/clip.mp4")))
        self.assertIsNone(cloud.eligible(self.sample(microedit={"final_duration":50})))

    def test_x_cloud_queries_only_x_queue_without_other_open_issues(self):
        from unittest.mock import MagicMock
        issue = self.sample()
        issue["number"] = 1002
        issue["created_at"] = (datetime.now(timezone.utc) -
                               timedelta(days=1)).isoformat()
        response = MagicMock()
        response.json.return_value = {
            "total_count": 1, "incomplete_results": False,
            "items": [issue],
        }
        with patch.dict("os.environ", {"GH_TOKEN": "unit-test"}), \
             patch.object(cloud.requests, "get", return_value=response) as get, \
             patch.object(cloud, "github", side_effect=AssertionError(
                 "Generic open-issue queue must not be scanned")):
            actual, payload = cloud.first_item()
        self.assertEqual(actual["number"], 1002)
        self.assertEqual(payload["account"], "lucasyahn")
        self.assertIn('in:title "[X-PUBLISH]"', get.call_args.kwargs["params"]["q"])
        self.assertEqual(get.call_args.kwargs["params"]["per_page"], 100)

    def test_x_cloud_fails_closed_on_incomplete_or_capped_search(self):
        from unittest.mock import MagicMock
        for result, expected in [
            ({"total_count": 1, "incomplete_results": True, "items": []},
             "X_GITHUB_OPEN_QUEUE_SEARCH_INCOMPLETE"),
            ({"total_count": 1000, "incomplete_results": False, "items": []},
             "X_GITHUB_OPEN_QUEUE_SEARCH_LIMIT"),
            ({"total_count": 2, "incomplete_results": False, "items": []},
             "X_GITHUB_OPEN_QUEUE_SEARCH_INCOMPLETE"),
        ]:
            with self.subTest(expected=expected):
                response = MagicMock()
                response.json.return_value = result
                with patch.dict("os.environ", {"GH_TOKEN": "unit-test"}), \
                     patch.object(cloud.requests, "get", return_value=response):
                    with self.assertRaisesRegex(RuntimeError, expected):
                        cloud.first_item()

    def test_window_failover_uses_recent_successful_authenticated_cloud(self):
        fresh=(datetime.now(timezone.utc)-timedelta(minutes=3)).isoformat()
        def repo(path):
            if path=="/actions/variables/ANTHARES_X_AUTOPUBLISH":return {"value":"1"}
            if "runs?" in path:return {"workflow_runs":[{"status":"completed","conclusion":"success","updated_at":fresh}]}
            raise AssertionError(path)
        with patch.object(local,"github",side_effect=repo):
            self.assertTrue(local.cloud_owns_queue())

    def test_local_resumes_immediately_when_cloud_unarmed_failed_or_stale(self):
        recent=datetime.now(timezone.utc)
        cases=[
            ("0",{"status":"completed","conclusion":"success","updated_at":recent.isoformat()}),
            ("1",{"status":"completed","conclusion":"failure","updated_at":recent.isoformat()}),
            ("1",{"status":"completed","conclusion":"success","updated_at":(recent-timedelta(minutes=45)).isoformat()}),
        ]
        for var,run in cases:
            with self.subTest(var=var,run=run):
                def repo(path):
                    if "/variables/" in path:return {"value":var}
                    return {"workflow_runs":[run]}
                with patch.object(local,"github",side_effect=repo):
                    self.assertFalse(local.cloud_owns_queue())

    def test_codeberg_smoke_must_never_steal_windows_queue(self):
        timestamp=datetime.now(timezone.utc).isoformat()
        def gh(path):
            if path.endswith("ANTHARES_X_CODEBERG_VERIFIED"):return {"value":"1"}
            if path.endswith("ANTHARES_X_AUTOPUBLISH"):return {"value":"0"}
            raise AssertionError(path)
        runs={"workflow_runs":[{"workflow_id":"x-codeberg-primary.yml",
                                 "status":"success","event":"workflow_dispatch",
                                 "stopped":timestamp}]}
        from unittest.mock import MagicMock
        with patch.object(local,"github",side_effect=gh),patch.object(local.requests,"get") as req:
            req.return_value.raise_for_status.return_value=None
            req.return_value.json.return_value=runs
            self.assertFalse(local.cloud_owns_queue())

    def test_cloud_claim_before_one_irreversible_post(self):
        source=(ROOT/"tools/x_github_anthares_browser_publisher.py").read_text(encoding="utf8")
        ast.parse(source)
        self.assertEqual(source.count("element.click();"),1)
        self.assertLess(source.index('durable("/claim-local"'),source.index("element.click();"))
        self.assertIn("X_DOUBLE_CLICK_DENIED",source)
        self.assertIn('X_VIDEO_CONFIRMED_V1',source)
        self.assertIn('verified_post_url(uri)',source)
        self.assertIn("X_CLOUD_RUNNER_IDENTITY_GUARD",source)

    def test_cloud_does_not_starve_windows_when_idle_unauthenticated(self):
        source=(ROOT/"tools/x_github_anthares_browser_publisher.py").read_text(encoding="utf8")
        self.assertIn('page = open_authenticated(context)',source)
        self.assertIn('X_GH_CLOUD_AUTHENTICATED_IDLE',source)
        self.assertIn("X_CLOUD_IDENTITY_NOT_PROVEN",source)

    def test_legacy_northflank_runner_requires_separate_explicit_arm(self):
        legacy=(ROOT/".github/workflows/x-durable-consumer.yml").read_text(encoding="utf8")
        new=(ROOT/".github/workflows/x-anthares-browser-cloud-publisher.yml").read_text(encoding="utf8")
        self.assertIn("ANTHARES_X_LEGACY_FALLBACK_ARM",legacy)
        self.assertIn("ANTHARES_X_AUTOPUBLISH",new)
        self.assertIn("runs-on: ubuntu-latest",new)
        self.assertIn("cancel-in-progress: false",new)

if __name__=="__main__":unittest.main()
