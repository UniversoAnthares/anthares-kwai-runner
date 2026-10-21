"""Fail-closed tests for Codeberg source redundancy and CI provider selection."""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]

class CodebergMirrorPolicyTests(unittest.TestCase):
    def test_ci_never_selects_quota_blocked_gitlab(self):
        conf=json.loads((ROOT/"ci-hub/executor-routing.json").read_text(encoding="utf-8"))
        self.assertNotIn("gitlab_ci",conf["ci_execution"]["priority"])
        self.assertFalse(conf["providers"]["gitlab_ci"]["ci_eligible"])
        self.assertFalse(conf["providers"]["codeberg_actions"]["ci_eligible"])
        self.assertFalse(conf["git_redundancy"]["codeberg"]["eligible_for_promotion"])
        self.assertEqual(conf["git_redundancy"]["recovery_order"][0],"codeberg")

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
