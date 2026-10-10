import unittest

from codespace_lifecycle import (
    CodespaceLifecycleError,
    choose_codespace,
    wake_existing_codespace,
)


class CodespaceLifecycleTests(unittest.TestCase):
    def test_choose_latest_matching_repository(self):
        rows = [
            {
                "name": "old-space",
                "last_used_at": "2026-10-09T00:00:00Z",
                "repository": {"full_name": "UniversoAnthares/anthares-kwai-runner"},
            },
            {
                "name": "new-space",
                "last_used_at": "2026-10-10T00:00:00Z",
                "repository": {"full_name": "UniversoAnthares/anthares-kwai-runner"},
            },
        ]
        self.assertEqual(choose_codespace(rows)["name"], "new-space")

    def test_missing_repository_fails_closed(self):
        with self.assertRaisesRegex(CodespaceLifecycleError, "codespace_for_repository_missing"):
            choose_codespace([])

    def test_available_codespace_does_not_receive_redundant_start(self):
        calls = []
        def transport(method, path, token):
            calls.append((method, path, token))
            return 200, {
                "codespaces": [{
                    "name": "anthares-a",
                    "state": "Available",
                    "last_used_at": "2026-10-10T20:00:00Z",
                    "repository": {"full_name": "UniversoAnthares/anthares-kwai-runner"},
                }]
            }
        result = wake_existing_codespace("private-token", transport=transport)
        self.assertEqual(result["action"], "already_available")
        self.assertFalse(result["token_exported"])
        self.assertEqual(len(calls), 1)
        self.assertNotIn("private-token", repr(result))

    def test_stopped_codespace_is_started(self):
        calls = []
        def transport(method, path, token):
            calls.append((method, path, token))
            if method == "GET":
                return 200, {
                    "codespaces": [{
                        "name": "anthares-a",
                        "state": "Shutdown",
                        "last_used_at": "2026-10-10T20:00:00Z",
                        "repository": {"full_name": "UniversoAnthares/anthares-kwai-runner"},
                    }]
                }
            return 200, {"name": "anthares-a", "state": "Available"}
        result = wake_existing_codespace("private-token", transport=transport)
        self.assertEqual(result["action"], "start_requested")
        self.assertEqual(result["state"], "Available")
        self.assertEqual(calls[1][0], "POST")
        self.assertEqual(calls[1][1], "/user/codespaces/anthares-a/start")
        self.assertNotIn("private-token", repr(result))

    def test_auth_failure_is_classified_without_token_leak(self):
        def transport(method, path, token):
            return 403, {"message": "Forbidden"}
        with self.assertRaises(CodespaceLifecycleError) as ctx:
            wake_existing_codespace("private-token", transport=transport)
        self.assertEqual(ctx.exception.code, "codespaces_token_unauthorized")
        self.assertNotIn("private-token", str(ctx.exception))

    def test_missing_token_fails_before_transport(self):
        with self.assertRaisesRegex(CodespaceLifecycleError, "codespaces_token_missing"):
            wake_existing_codespace("")


if __name__ == "__main__":
    unittest.main()
