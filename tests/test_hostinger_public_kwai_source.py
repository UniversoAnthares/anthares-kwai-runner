"""Isolated regressions: public GitHub Kwai source may not inherit a private token helper.

This test extracts only run() from Hostinger mirror; no network, Git or account access.
"""
import ast
import pathlib
import types
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "tools" / "hostinger" / "git-mirror-hostinger.py"
PUBLIC = "https://github.com/UniversoAnthares/anthares-kwai-runner.git"

def harness(stderr="", code=0):
    module = ast.parse(SOURCE.read_text(encoding="utf-8"))
    matches = [n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == "run"]
    if len(matches) != 1:
        raise AssertionError("Unexpected mirror run function")
    calls = []
    def fake_run(args, **kwargs):
        calls.append((list(args), dict(kwargs)))
        return types.SimpleNamespace(returncode=code, stdout="REFS_OK", stderr=stderr)
    tok = types.SimpleNamespace(is_file=lambda: True, stat=lambda: types.SimpleNamespace(st_size=9))
    scope = {
        "env": {"GIT_ASKPASS": "/private/other-helper", "GIT_TERMINAL_PROMPT": "0"},
        "source_key_repo": lambda args: None,
        "token_file": tok,
        "github_askpass": "/private/readonly-token-helper",
        "subprocess": types.SimpleNamespace(PIPE=-1, run=fake_run),
    }
    exec(compile(ast.Module(body=matches, type_ignores=[]), str(SOURCE), "exec"), scope)
    return scope["run"], calls

class PublicKwaiSourceTests(unittest.TestCase):
    def test_anonymous_public_access(self):
        run, calls = harness()
        self.assertEqual(run(["git", "ls-remote", PUBLIC], github=True), "REFS_OK")
        self.assertEqual(calls[0][1]["env"]["GIT_ASKPASS"], "/bin/false")
        self.assertEqual(calls[0][1]["env"]["GIT_TERMINAL_PROMPT"], "0")

    def test_private_credential_helper_unchanged(self):
        run, calls = harness()
        self.assertEqual(run(["git", "ls-remote", "https://github.com/UniversoAnthares/other.git"], github=True), "REFS_OK")
        self.assertEqual(calls[0][1]["env"]["GIT_ASKPASS"], "/private/readonly-token-helper")

    def test_public_http403_is_classified_without_echoing_stderr(self):
        run, _ = harness("fatal: the requested URL returned error: 403 [private diagnostic data]", 128)
        with self.assertRaisesRegex(RuntimeError, "^PUBLIC_GITHUB_HTTP_403$"):
            run(["git", "ls-remote", PUBLIC], github=True)

    def test_public_dns_is_classified(self):
        run, _ = harness("fatal: unable to access: Could not resolve host: github.com", 128)
        with self.assertRaisesRegex(RuntimeError, "^PUBLIC_GITHUB_DNS_UNAVAILABLE$"):
            run(["git", "ls-remote", PUBLIC], github=True)

    def test_quota_preserves_specific_error(self):
        run, _ = harness("fork failed: Resource temporarily unavailable", 128)
        with self.assertRaisesRegex(RuntimeError, "^HOSTING_PROCESS_LIMIT$"):
            run(["git", "ls-remote", PUBLIC], github=True)

    def test_other_source_unmodified_failure(self):
        run, _ = harness("ordinary failure", 128)
        with self.assertRaisesRegex(RuntimeError, "^GIT_FAILED_128$"):
            run(["git", "ls-remote", "https://github.com/UniversoAnthares/other.git"], github=True)

if __name__ == "__main__":
    unittest.main()
