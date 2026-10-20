"""Check independent cloud triggers preserve the OIDC caller boundary."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import cortes_tiktok_hosted_publish as h

class CloudTriggerTest(unittest.TestCase):
    def make_event(self, **kwargs):
        data={"workflow_run":{"name":"Anthares Core Supervisor","conclusion":"success",
            "head_branch":"main","head_repository":{"full_name":"UniversoAnthares/anthares-kwai-runner"}}}
        data["workflow_run"].update(kwargs)
        f=tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",suffix=".json",delete=False)
        try:json.dump(data,f);f.close();return f.name
        except Exception:
            f.close();raise

    def test_schedule_and_manual_main(self):
        for event in ("schedule","workflow_dispatch"):
            self.assertTrue(h.trusted_workflow_event(event,"refs/heads/main",""))

    def test_untrusted_branches_denied(self):
        for event in ("schedule","workflow_dispatch","workflow_run"):
            self.assertFalse(h.trusted_workflow_event(event,"refs/heads/dev","/tmp/does-not-matter"))

    def test_successful_supervisor_allowed(self):
        f=self.make_event()
        try:self.assertTrue(h.trusted_workflow_event("workflow_run","refs/heads/main",f))
        finally:os.unlink(f)

    def test_failed_external_and_branch_denied(self):
        for changed in ({"conclusion":"failure"},{"head_branch":"test"},
                        {"head_repository":{"full_name":"other/repository"}},
                        {"name":"Other Workflow"}):
            f=self.make_event(**changed)
            try:self.assertFalse(h.trusted_workflow_event("workflow_run","refs/heads/main",f))
            finally:os.unlink(f)

    def test_pull_request_never_publish(self):
        self.assertFalse(h.trusted_workflow_event("pull_request","refs/heads/main",""))

    def test_followup_emitted_only_when_pending(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as root:
            output=str(Path(root)/"out.txt")
            with patch.dict(os.environ,{"GITHUB_OUTPUT":output}), patch.object(h.q,"qcall",return_value={"ok":True,"count":{"queued":3}}):
                h.request_followup_if_pending({})
            self.assertEqual(Path(output).read_text().strip(),"queue_followup=true")

    def test_followup_not_emitted_for_empty_or_failed_status(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as root:
            output=str(Path(root)/"out.txt")
            for response in ({"ok":True,"count":{"queued":0}},{"ok":False},{"ok":True,"count":{}}):
                with patch.dict(os.environ,{"GITHUB_OUTPUT":output}), patch.object(h.q,"qcall",return_value=response):
                    h.request_followup_if_pending({})
            self.assertFalse(Path(output).exists())

    def test_invalid_payload_fails_closed(self):
        f=tempfile.NamedTemporaryFile(mode="w",delete=False)
        f.write("not json");f.close()
        try:self.assertFalse(h.trusted_workflow_event("workflow_run","refs/heads/main",f.name))
        finally:os.unlink(f.name)

if __name__=="__main__":
    unittest.main()
