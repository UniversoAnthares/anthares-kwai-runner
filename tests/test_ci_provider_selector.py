"""Deterministic simulation of hosted CI failover; never dispatches."""
import copy
import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from ci_provider_selector import choose

NOW = dt.datetime(2026, 10, 26, 21, tzinfo=dt.timezone.utc)
SHA = "a" * 40
ROUTING = {"ci_execution": {"priority": ["github_actions_public", "bitrise", "appveyor", "gitlab_ci"]},
           "providers": {p: {"active": True, "ci_eligible": True}
                         for p in ("github_actions_public", "bitrise", "appveyor", "gitlab_ci")}}
RECORDED = {"rules": {"retired_never_route": []},
            "providers": {p: {"eligible": True} for p in ROUTING["providers"]}}


def proof():
    return {"healthy": True, "ready": True, "authenticated": True,
            "free_quota_ok": True, "runner_available": True,
            "source_sha": SHA, "successful_hosted_run_id": "run-123",
            "observed_at_utc": NOW.isoformat()}


class CIProviderSelectionTests(unittest.TestCase):
    def test_first_fresh_candidate(self):
        result = choose(ROUTING, RECORDED, {"github_actions_public": proof()}, source_sha=SHA, now=NOW)
        self.assertEqual(result["provider"], "github_actions_public")
        self.assertFalse(result["dispatched"])

    def test_appveyor_http500_moves_to_last(self):
        result = choose(ROUTING, RECORDED, {"gitlab_ci": proof()}, source_sha=SHA,
                        previous="appveyor", outcome="http500", now=NOW)
        self.assertEqual(result["provider"], "gitlab_ci")

    def test_timeout_requires_reconciliation(self):
        self.assertEqual(choose(ROUTING, RECORDED, {"gitlab_ci": proof()}, source_sha=SHA,
                                previous="appveyor", outcome="timeout", now=NOW)["action"], "STOP")

    def test_mutation_boundary_blocks_fallback(self):
        self.assertEqual(choose(ROUTING, RECORDED, {"gitlab_ci": proof()}, source_sha=SHA,
                                previous="appveyor", outcome="http500", mutation_started=True, now=NOW)["action"], "STOP")

    def test_inactive_bitrise_skipped(self):
        cfg = copy.deepcopy(ROUTING)
        cfg["providers"]["bitrise"]["active"] = False
        result = choose(cfg, RECORDED, {"bitrise": proof(), "appveyor": proof()}, source_sha=SHA,
                        previous="github_actions_public", outcome="confirmed_failure", now=NOW)
        self.assertEqual(result["provider"], "appveyor")

    def test_ineligible_appveyor_skipped(self):
        cfg = copy.deepcopy(ROUTING)
        cfg["providers"]["appveyor"]["ci_eligible"] = False
        status = copy.deepcopy(RECORDED)
        status["providers"]["appveyor"]["eligible"] = False
        result = choose(cfg, status, {"appveyor": proof(), "gitlab_ci": proof()}, source_sha=SHA,
                        previous="bitrise", outcome="confirmed_failure", now=NOW)
        self.assertEqual(result["provider"], "gitlab_ci")

    def test_quota_and_sha_fail_closed(self):
        bad = proof()
        bad["free_quota_ok"] = False
        self.assertEqual(choose(ROUTING, RECORDED, {"github_actions_public": bad},
                                source_sha=SHA, now=NOW)["action"], "NONE")
        bad = proof()
        bad["source_sha"] = "b" * 40
        self.assertEqual(choose(ROUTING, RECORDED, {"github_actions_public": bad},
                                source_sha=SHA, now=NOW)["action"], "NONE")

    def test_stale_evidence_fails_closed(self):
        bad = proof()
        bad["observed_at_utc"] = (NOW - dt.timedelta(seconds=601)).isoformat()
        self.assertEqual(choose(ROUTING, RECORDED, {"github_actions_public": bad},
                                source_sha=SHA, now=NOW)["action"], "NONE")

    def test_missing_status_no_candidate(self):
        self.assertEqual(choose(ROUTING, RECORDED, {}, source_sha=SHA, now=NOW)["action"], "NONE")

    def test_bad_order_rejected(self):
        cfg = copy.deepcopy(ROUTING)
        cfg["ci_execution"]["priority"].append("appveyor")
        self.assertEqual(choose(cfg, RECORDED, {}, source_sha=SHA, now=NOW)["action"], "STOP")

    def test_unknown_previous_rejected(self):
        self.assertEqual(choose(ROUTING, RECORDED, {}, source_sha=SHA, previous="nonexistent",
                                outcome="confirmed_failure", now=NOW)["action"], "STOP")


if __name__ == "__main__":
    unittest.main()
