"""Offline AI-04 circuit-breaker tests: no secrets, tokens, network or paid calls."""
import unittest

from ai_hub.eligibility_breaker import (
    CircuitBreaker, ProviderPolicy, UpstreamOutcomeError,
    NoEligibleProvider, ProvidersTemporarilyUnavailable, dispatch,
)


def cfg(name, *, tasks=("text",), authorized=True, credential=True,
        quota=True, budget=True, paid=False, approve_paid=False):
    return ProviderPolicy(name, frozenset(tasks), authorized, credential, quota,
                          budget, paid, approve_paid)


class EligibilityTests(unittest.TestCase):
    def setUp(self):
        self.now = [100.0]
        self.cb = CircuitBreaker(clock=lambda: self.now[0])

    def test_fallback_after_quota_limit_only_to_authorized_provider(self):
        seen = []
        def invoke(name):
            seen.append(name)
            if name == "gemini":
                raise UpstreamOutcomeError(429)
            return "accepted"
        actual, provider, attempts = dispatch("text", [cfg("gemini"), cfg("groq")],
                                               self.cb, invoke)
        self.assertEqual((actual, provider, attempts),
                         ("accepted", "groq", ["gemini", "groq"]))
        self.assertTrue(self.cb.status("gemini")["open"])
        self.assertEqual(seen, ["gemini", "groq"])

    def test_second_request_skips_open_quota_provider(self):
        self.cb.record_failure("gemini", http_status=429)
        result = dispatch("text", [cfg("gemini"), cfg("groq")], self.cb, lambda name: name)
        self.assertEqual(result[1:], ("groq", ["groq"]))

    def test_quota_cooldown_reopens_after_reset(self):
        self.cb.record_failure("gemini", http_status=429, retry_after=1800)
        self.now[0] += 1799
        self.assertFalse(self.cb.allowed("gemini"))
        self.now[0] += 2
        self.assertTrue(self.cb.allowed("gemini"))

    def test_payment_block_does_not_route_unapproved_paid_provider(self):
        attempted = []
        def invoke(name):
            attempted.append(name)
            raise UpstreamOutcomeError(402)
        with self.assertRaises(ProvidersTemporarilyUnavailable):
            dispatch("text", [cfg("gemini"), cfg("paid_alt", paid=True)], self.cb, invoke)
        self.assertEqual(attempted, ["gemini"])
        self.assertEqual(self.cb.status("gemini")["reason"], "payment_denied")

    def test_paid_fallback_needs_explicit_approval(self):
        result = dispatch("text", [cfg("paid_alt", paid=True, approve_paid=True)],
                          self.cb, lambda n: n)
        self.assertEqual(result[1], "paid_alt")

    def test_no_verified_quota_must_fail_closed(self):
        with self.assertRaises(NoEligibleProvider):
            dispatch("text", [cfg("groq", quota=False)], self.cb,
                     lambda n: self.fail("unexpected_upstream_call"))

    def test_wrong_task_stt_cannot_fallback_to_text_provider(self):
        with self.assertRaises(NoEligibleProvider):
            dispatch("stt", [cfg("gemini", tasks=("text",))], self.cb, lambda n: n)

    def test_server_circuit_opens_only_after_threshold(self):
        self.assertEqual(self.cb.record_failure("groq", http_status=503), "transient_failure")
        self.assertTrue(self.cb.allowed("groq"))
        self.assertEqual(self.cb.record_failure("groq", http_status=504), "server_cooldown")
        self.assertFalse(self.cb.allowed("groq"))
        self.now[0] += 91
        self.assertTrue(self.cb.allowed("groq"))

    def test_timeout_then_success_resets_counter(self):
        self.cb.record_failure("groq", timeout=True)
        self.cb.record_success("groq")
        self.assertEqual(self.cb.status("groq")["consecutive_server_errors"], 0)

    def test_forbidden_upstream_refuses_fallback(self):
        seen = []
        def invoke(name):
            seen.append(name)
            raise UpstreamOutcomeError(403)
        with self.assertRaises(UpstreamOutcomeError):
            dispatch("text", [cfg("gemini"), cfg("groq")], self.cb, invoke)
        self.assertEqual(seen, ["gemini"])
        self.assertEqual(self.cb.status("gemini")["reason"], "auth_denied")

    def test_duplicates_rejected(self):
        with self.assertRaises(ValueError):
            dispatch("text", [cfg("groq"), cfg("groq")], self.cb, lambda n: n)

    def test_not_authorized_must_not_be_attempted(self):
        result = dispatch("text", [cfg("unapproved", authorized=False), cfg("groq")],
                          self.cb, lambda n: n)
        self.assertEqual(result[2], ["groq"])


if __name__ == "__main__":
    unittest.main()
