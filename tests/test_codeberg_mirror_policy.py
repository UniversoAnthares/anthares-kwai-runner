"""Fail-closed tests for Codeberg source redundancy and CI provider selection."""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]

class CodebergMirrorPolicyTests(unittest.TestCase):
    def test_gitlab_stays_available_as_quota_gated_standby(self):
        conf=json.loads((ROOT/"ci-hub/executor-routing.json").read_text(encoding="utf-8"))
        self.assertIn("gitlab_ci",conf["ci_execution"]["priority"])
        self.assertGreater(conf["ci_execution"]["priority"].index("gitlab_ci"),conf["ci_execution"]["priority"].index("codeberg_actions"))
        self.assertTrue(conf["providers"]["gitlab_ci"]["active"])
        self.assertFalse(conf["providers"]["gitlab_ci"]["ci_eligible"])
        self.assertEqual(conf["providers"]["gitlab_ci"]["status"],"STANDBY_BLOCKED_QUOTA_AUTO_RECHECK")
        self.assertFalse(conf["providers"]["codeberg_actions"]["ci_eligible"])
        self.assertFalse(conf["git_redundancy"]["codeberg"]["eligible_for_promotion"])
        self.assertEqual(conf["git_redundancy"]["recovery_order"][0],"codeberg")

    def test_appveyor_penultimate_and_fail_closed(self):
        routing=json.loads((ROOT/"ci-hub/executor-routing.json").read_text(encoding="utf-8"))
        status=json.loads((ROOT/"ci-hub/provider-status.json").read_text(encoding="utf-8"))
        priority=routing["ci_execution"]["priority"]
        self.assertEqual(priority[-2], "appveyor")
        self.assertEqual(len(priority), len(set(priority)))
        self.assertFalse(routing["providers"]["appveyor"]["ci_eligible"])
        self.assertFalse(status["providers"]["appveyor"]["eligible"])
        self.assertIn("HTTP500", routing["providers"]["appveyor"]["status"])
        self.assertFalse(routing["providers"]["appveyor_linux_chromium"]["browser_backend_eligible"])

    def test_bitrise_smoke_is_configured_but_not_activated(self):
        routing=json.loads((ROOT/"ci-hub/executor-routing.json").read_text(encoding="utf-8"))
        status=json.loads((ROOT/"ci-hub/provider-status.json").read_text(encoding="utf-8"))
        priority=routing["ci_execution"]["priority"]
        self.assertIn("bitrise", priority)
        self.assertEqual(priority.index("bitrise"), priority.index("appveyor") - 1)
        self.assertFalse(routing["providers"]["bitrise"]["active"])
        self.assertFalse(routing["providers"]["bitrise"]["ci_eligible"])
        self.assertFalse(status["providers"]["bitrise"]["eligible"])
        yaml=(ROOT/"bitrise.yml").read_text(encoding="utf-8")
        smoke=yaml.split("  anthares_ci_smoke:", 1)[1]
        self.assertIn("BITRISE_HOSTED_SMOKE=PASS", smoke)
        self.assertIn("ci/shared/provider-smoke.sh", smoke)
        self.assertNotIn("deploy-to-bitrise-io@", smoke)
        self.assertNotIn("avd-manager@", smoke)

    def test_mirror_rejects_missing_credentials_and_divergence(self):
        w=(ROOT/".github/workflows/mirror-codeberg.yml").read_text(encoding="utf-8")
        self.assertIn("CODEBERG_MIRROR_AUTH_REQUIRED",w)
        self.assertIn("CODEBERG_DIVERGED_NO_PUSH",w)
        self.assertIn("CODEBERG_POST_PUSH_SHA_MISMATCH",w)
        self.assertIn("CODEBERG_MAIN_FAST_FORWARD_VERIFIED=PASS",w)
        self.assertIn("git merge-base --is-ancestor",w)
        self.assertNotIn("--force",w)
        self.assertNotIn("exit 0\n          fi\n          git remote add",w)

    def test_only_main_mirrored_and_coalesced(self):
        w=(ROOT/".github/workflows/mirror-codeberg.yml").read_text(encoding="utf-8")
        self.assertIn("branches: [main]",w)
        self.assertIn("cancel-in-progress: true",w)
        self.assertIn("schedule:",w)
        self.assertNotIn("refs/remotes/origin/*:refs/heads/*",w)

if __name__=="__main__":
    unittest.main()
