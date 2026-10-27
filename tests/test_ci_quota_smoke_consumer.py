"""Live quota controller guard regression, no network or remote cancellation."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location("quota_smoke_consumer", TOOLS/"ci_quota_smoke_consumer.py")
consumer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(consumer)

class SmokeGuardTests(unittest.TestCase):
    def setup_event(self,payload):
        temp=tempfile.TemporaryDirectory()
        file=Path(temp.name)/"github-event.json"
        file.write_text(json.dumps({"client_payload":payload}),encoding="utf-8")
        return temp,{"GITHUB_TOKEN":"not-a-real-token",
                     "GITHUB_REPOSITORY":"UniversoAnthares/anthares-kwai-runner",
                     "GITHUB_EVENT_PATH":str(file)}

    def test_auth_required(self):
        with patch.dict(os.environ,{},clear=True):
            self.assertEqual(consumer.main(),2)

    def test_untrusted_event_denied_before_api(self):
        temp,env=self.setup_event({"mode":"live","provider":"github_actions",
                "repo":"UniversoAnthares/anthares-kwai-runner",
                "run_id":"123","code":"ci_quota_exceeded"})
        try:
            with patch.dict(os.environ,env,clear=True):
                self.assertEqual(consumer.main(),2)
        finally:temp.cleanup()

    def test_foreign_repository_denied(self):
        temp,env=self.setup_event({"mode":"synthetic_smoke","provider":"github_actions",
                "repo":"other/foreign","run_id":"123","code":"ci_quota_exceeded"})
        try:
            with patch.dict(os.environ,env,clear=True):
                self.assertEqual(consumer.main(),2)
        finally:temp.cleanup()

    def test_approved_simulation_requires_allowlisted_live_run(self):
        temp,env=self.setup_event({"mode":"synthetic_smoke","provider":"github_actions",
                "repo":"UniversoAnthares/anthares-kwai-runner",
                "run_id":"123","code":"ci_quota_exceeded"})
        class Fake:
            url="https://api.github.com/repos/UniversoAnthares/anthares-kwai-runner/actions/runs/123"
            headers={}
        try:
            with patch.dict(os.environ,env,clear=True), \
                 patch.object(consumer,"GitHubActionsRun",return_value=Fake()), \
                 patch.object(consumer,"http_json",return_value=(200,{"name":"unexpected-workflow","repository":{"full_name":env["GITHUB_REPOSITORY"]}})):
                self.assertEqual(consumer.main(),2)
        finally:temp.cleanup()

if __name__=="__main__":unittest.main()
