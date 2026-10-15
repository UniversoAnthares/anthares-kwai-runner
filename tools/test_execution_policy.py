import unittest

from execution_policy import Action, decide, validate_surface


class ExecutionPolicyTests(unittest.TestCase):
    def test_remote_surface_is_exclusive(self):
        self.assertTrue(validate_surface("remote_control", "anthares_remote"))
        for provider in ("render", "tinyfish", "circleci", "browserless", "github_actions"):
            self.assertFalse(validate_surface("remote_control", provider))

    def test_browser_surface_is_exclusive(self):
        self.assertTrue(validate_surface("browser", "anthares_browser"))
        for provider in ("browserless", "tinyfish", "render", "cloudflare_browser_rendering"):
            self.assertFalse(validate_surface("browser", provider))

    def test_retired_provider_migrates(self):
        for provider in ("render", "tinyfish", "circleci", "browserless"):
            self.assertEqual(decide(provider, "down").action, Action.MIGRATE_PROVIDER)

    def test_quota_block_migrates_without_repair(self):
        decision = decide("anthares_browser", "timeout", quota_state="BLOCKED_QUOTA")
        self.assertEqual(decision.action, Action.MIGRATE_PROVIDER)
        self.assertFalse(decision.retry_same_provider)

    def test_anthares_component_failure_repairs(self):
        decision = decide("anthares_remote", "protocol", quota_state="READY")
        self.assertEqual(decision.action, Action.REPAIR_ANTHARES)
        self.assertTrue(decision.retry_same_provider)

    def test_manual_security_boundary(self):
        self.assertEqual(decide("anthares_browser", "mfa").action, Action.MANUAL_OWNER)
        self.assertEqual(decide("anthares_browser", "captcha").action, Action.MANUAL_OWNER)

    def test_implementation_agent_when_available(self):
        decision = decide("github_actions", "repository_refactor", agent_available=True)
        self.assertEqual(decision.action, Action.USE_IMPLEMENTATION_AGENT)

    def test_unknown_fails_closed(self):
        self.assertEqual(decide("some_provider", "mystery").action, Action.FAIL_CLOSED)


if __name__ == "__main__":
    unittest.main()
