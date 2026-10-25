"""Offline QA tests for AI-01 Groq capability auditor; no endpoint or secret."""
import io
import json
import unittest
from unittest import mock

try:
    from ai_hub import qa_ai01_groq_certifier as c
except ImportError:
    import qa_ai01_groq_certifier as c


def good_payload():
    return {
        "model": c.MODEL,
        "usage": {"prompt_tokens": 53, "completion_tokens": 18},
        "choices": [{"message": {"content": '{"soma":7,"idioma":"pt-BR","fonte":"sintetica"}'}}],
    }


class GroqAI01QATests(unittest.TestCase):
    def test_nominal_quality_pass_still_partial(self):
        r = c.parse_result(200, good_payload(), {
            "X-RateLimit-Limit-Requests": "1000",
            "x-ratelimit-remaining-tokens": "2000",
            "X-Fictional-Secret": "never-export",
        }, 423)
        self.assertTrue(r["upstream_quality_pass"])
        self.assertEqual(r["certification"], "PARTIAL")
        self.assertEqual(r["elapsed_ms"], 423)
        self.assertNotIn("X-Fictional-Secret", json.dumps(r))
        self.assertFalse(r["account_quota_verified"])
        self.assertFalse(r["account_spend_cap_verified"])

    def test_cost_estimate_uses_correct_units(self):
        self.assertAlmostEqual(c.estimate_cost_usd(1_000_000, 1_000_000), 0.375)
        self.assertLess(c.max_expected_cost_usd(), 0.0001)

    def test_http_429_does_not_imply_success(self):
        r = c.parse_result(429, good_payload(), {"Retry-After": "60"}, 300)
        self.assertFalse(r["upstream_quality_pass"])
        self.assertEqual(r["reason"], "no_valid_authenticated_success")
        self.assertEqual(r["rate_limit_headers"]["retry-after"], "60")

    def test_missing_model_is_rejected(self):
        p = good_payload()
        p["model"] = "another-model"
        self.assertFalse(c.parse_result(200, p, {}, 100)["upstream_quality_pass"])

    def test_plain_text_is_rejected(self):
        p = good_payload()
        p["choices"][0]["message"]["content"] = "Sete."
        self.assertFalse(c.parse_result(200, p, {}, 100)["upstream_quality_pass"])

    def test_extra_json_properties_are_rejected(self):
        p = good_payload()
        p["choices"][0]["message"]["content"] = '{"soma":7,"idioma":"pt-BR","fonte":"sintetica","bonus":1}'
        self.assertFalse(c.parse_result(200, p, {}, 100)["upstream_quality_pass"])

    def test_missing_usage_is_rejected(self):
        p = good_payload()
        p.pop("usage")
        self.assertEqual(c.parse_result(200, p, {}, 100)["reason"], "missing_usage_or_choices")

    def test_negative_or_boolean_usage_rejected(self):
        for invalid in [-1, True, "53"]:
            p = good_payload()
            p["usage"]["prompt_tokens"] = invalid
            self.assertEqual(c.parse_result(200, p, {}, 10)["reason"], "invalid_usage")

    def test_missing_key_never_makes_request(self):
        with mock.patch.object(c.request, "urlopen") as connection:
            with self.assertRaisesRegex(ValueError, "missing_authorized_credential"):
                c.single_live_call("", max_budget_usd=0.0001)
            connection.assert_not_called()

    def test_budget_rejection_before_request(self):
        with mock.patch.object(c.request, "urlopen") as connection:
            with self.assertRaisesRegex(ValueError, "conservative_budget_too_small"):
                c.single_live_call("x" * 25, max_budget_usd=0.000001)
            connection.assert_not_called()

    def test_default_cli_calls_no_network(self):
        with mock.patch("sys.argv", ["auditor"]), \
             mock.patch.object(c.request, "urlopen") as connection, \
             mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            self.assertEqual(c.main(), 0)
            r = json.loads(out.getvalue())
            self.assertEqual(r["certification"], "NOT_TESTED")
            self.assertEqual(r["calls_attempted"], 0)
            connection.assert_not_called()

    def test_bad_live_http_payload_not_certified(self):
        with mock.patch.object(c.request, "urlopen") as connection:
            fake = mock.MagicMock()
            fake.__enter__.return_value = fake
            fake.status = 200
            fake.headers.items.return_value = []
            fake.read.return_value = b'{"model":"wrong","usage":{"prompt_tokens":1,"completion_tokens":2},"choices":[{"message":{"content":"{}"}}]}'
            connection.return_value = fake
            r = c.single_live_call("x" * 25, 0.0001)
            self.assertFalse(r["upstream_quality_pass"])
            self.assertEqual(r["calls_attempted"], 1)
            connection.assert_called_once()


if __name__ == "__main__":
    unittest.main()
