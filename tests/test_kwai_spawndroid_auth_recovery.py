"""Agent 05 synthetic contract tests: never allocate a SpawnDroid runner."""
import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from tools import kwai_spawndroid_auth_recovery as guard


def req(account="universoanthares", session="session00001", now=1000):
    package = guard.ACCOUNT_PACKAGES[account]
    return {
        "account": account,
        "package": package,
        "session_id": session,
        "provider_session_state": "ready",
        "ledger_state": "settled",
        "observation": {
            "source": "appium_live",
            "session_id": session,
            "foreground_package": package,
            "observed_at_epoch": now,
            "profile_handle": "@" + account,
            "owner_edit_control": True,
            "publisher_entry_visible": True,
            "challenge_required": False,
        },
    }


class AuthRecoveryContract(unittest.TestCase):
    NOW = 1000

    def evaluate(self, request):
        return guard.decide(request, now_epoch=self.NOW)

    def test_both_accounts_independently_verified(self):
        for account in ("universoanthares", "lucasrosalem"):
            with self.subTest(account=account):
                outcome = self.evaluate(req(account))
                self.assertEqual(outcome["status"], "AUTHENTICATED_CURRENT_SESSION")
                self.assertTrue(outcome["identity_verified_current_session"])
                self.assertTrue(outcome["publisher_ui_verified_current_session"])
                self.assertFalse(outcome["publication_authorized"])
                self.assertFalse(outcome["cloud_cutover_authorized"])

    def test_successive_sessions_require_fresh_identity_for_both_accounts(self):
        for account in guard.ACCOUNT_PACKAGES:
            with self.subTest(account=account):
                first = req(account, session="session00001")
                self.assertEqual(self.evaluate(first)["status"], "AUTHENTICATED_CURRENT_SESSION")
                second = req(account, session="session00002")
                second["observation"] = first["observation"]
                self.assertEqual(self.evaluate(second)["reason_code"], "STALE_OR_CROSS_SESSION_PROOF")
                self.assertFalse(self.evaluate(second)["identity_verified_current_session"])
                second["observation"] = req(account, session="session00002")["observation"]
                self.assertEqual(self.evaluate(second)["status"], "AUTHENTICATED_CURRENT_SESSION")

    def test_no_restoration_from_previous_android_snapshot(self):
        request = req()
        request.pop("observation")
        request["prior_session_id"] = "session00000"
        request["prior_authenticated"] = True
        request["appium:noReset"] = True
        self.assertEqual(self.evaluate(request)["status"], "AUTH_REQUIRED")

    def test_mismatch_account_handle_blocks(self):
        for account, other in (("universoanthares", "lucasrosalem"),
                               ("lucasrosalem", "universoanthares")):
            request = req(account)
            request["observation"]["profile_handle"] = other
            self.assertEqual(self.evaluate(request)["status"], "AUTH_REQUIRED")

    def test_package_swap_blocked_before_identity(self):
        request = req("lucasrosalem")
        request["package"] = "com.kwai.video"
        self.assertEqual(self.evaluate(request)["reason_code"],
                         "APP_ACCOUNT_PACKAGE_MISMATCH")

    def test_ui_foreground_swap_blocked(self):
        request = req()
        request["observation"]["foreground_package"] = "kwai.lite.video"
        self.assertEqual(self.evaluate(request)["reason_code"], "FOREGROUND_APP_MISMATCH")

    def test_profile_without_owner_action_is_not_authentication(self):
        request = req()
        request["observation"]["owner_edit_control"] = False
        self.assertEqual(self.evaluate(request)["status"], "AUTH_REQUIRED")

    def test_composer_access_must_be_observed(self):
        request = req()
        request["observation"]["publisher_entry_visible"] = False
        d = self.evaluate(request)
        self.assertEqual(d["status"], "AUTHENTICATED_UI_PENDING")
        self.assertFalse(d["publisher_ui_verified_current_session"])

    def test_stale_or_future_observation(self):
        for observed_at in (879, 1006, "1000", True):
            request = req()
            request["observation"]["observed_at_epoch"] = observed_at
            self.assertEqual(self.evaluate(request)["status"], "REAUTH_REQUIRED")

    def test_exact_evidence_age_limit(self):
        request = req()
        request["observation"]["observed_at_epoch"] = 880
        self.assertEqual(self.evaluate(request)["status"], "AUTHENTICATED_CURRENT_SESSION")

    def test_untrusted_source_blocked(self):
        request = req()
        request["observation"]["source"] = "copied_cookie_archive"
        self.assertEqual(self.evaluate(request)["reason_code"], "EVIDENCE_SOURCE_INVALID")

    def test_mfa_otp_captcha_stop_without_bypass(self):
        for error in ("otp_required", "mfa_required",
                      "captcha_required", "device_approval_required"):
            request = req()
            request["failure"] = error
            with self.subTest(error=error):
                d = self.evaluate(request)
                self.assertEqual(d["status"], "HUMAN_REQUIRED")
                self.assertFalse(d["automatic_retry_allowed"])
        request = req()
        request["observation"]["challenge_required"] = True
        self.assertEqual(self.evaluate(request)["status"], "HUMAN_REQUIRED")

    def test_errors_classified_without_repeated_publication(self):
        expected = {
            "401": "REAUTH_REQUIRED", "403": "SECURITY_BLOCKED",
            "402": "QUOTA_CANCEL_REQUIRED", "429": "RUNNER_SLOT_BUSY",
            "502": "PROVIDER_UNAVAILABLE", "503": "PROVIDER_UNAVAILABLE",
            "auth_revoked": "REAUTH_REQUIRED",
            "session_not_found": "SESSION_TERMINAL",
            "transport_timeout": "SESSION_UNCERTAIN",
        }
        for error, state in expected.items():
            request = req()
            request["failure"] = error
            with self.subTest(error=error):
                d = self.evaluate(request)
                self.assertEqual(d["status"], state)
                self.assertFalse(d["publication_authorized"])
                self.assertFalse(d["automatic_retry_allowed"])

    def test_uncertain_publication_priority_over_valid_auth_and_errors(self):
        for ledger in ("started", "uncertain", "cancel_unconfirmed", "reconcile_required", None, "unknown"):
            request = req()
            request["ledger_state"] = ledger
            request["failure"] = "quota_exhausted"
            self.assertEqual(self.evaluate(request)["status"], "RECONCILE_REQUIRED")

    def test_provider_not_ready_blocks(self):
        request = req()
        request["provider_session_state"] = "stopped"
        self.assertEqual(self.evaluate(request)["status"], "SESSION_NOT_READY")

    def test_invalid_account_session_and_input_block(self):
        for request in (None, {}, {"account": "unknown"}, req()):
            if isinstance(request, dict) and request.get("account") == "universoanthares":
                request["session_id"] = "bad secret /session"
            self.assertEqual(self.evaluate(request)["status"], "BLOCKED")

    def test_no_secrets_in_output(self):
        request = req()
        request.update({"password": "SENSITIVE_PASSWORD", "cookie": "SENSITIVE_COOKIE",
                        "token": "SENSITIVE_TOKEN", "otp": "SENSITIVE_OTP"})
        out = json.dumps(self.evaluate(request))
        for secret in request.values():
            if isinstance(secret, str) and secret.startswith("SENSITIVE"):
                self.assertNotIn(secret, out)

    def test_cli_fails_closed_without_logging_input(self):
        payload = {"account": "unknown", "token": "SECRET_TOKEN_VALUE"}
        with patch("sys.stdin", io.StringIO(json.dumps(payload))), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(guard.main(), 2)
        self.assertNotIn("SECRET_TOKEN_VALUE", output.getvalue())
        self.assertEqual(json.loads(output.getvalue())["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
