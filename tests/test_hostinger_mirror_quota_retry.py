"""Isolated contract tests for the existing Hostinger Forgejo mirror NPROC retry.

Never import/execute the complete mirror module: its top-level code accesses repos.
Run: python3 -m unittest tests/test_hostinger_mirror_quota_retry.py -v
"""
import ast
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "tools" / "hostinger" / "git-mirror-hostinger.py"


def load_retry(verify, timer):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    matched = [n for n in tree.body if isinstance(n, ast.FunctionDef)
               and n.name == "verify_with_quota_retry"]
    if len(matched) != 1:
        raise AssertionError("Missing or ambiguous retry wrapper")
    scope = {"verify_repo": verify, "time": timer}
    code = compile(ast.Module(body=matched, type_ignores=[]), str(SOURCE), "exec")
    exec(code, scope)
    return scope["verify_with_quota_retry"]


class Timer:
    def __init__(self):
        self.delays = []

    def sleep(self, seconds):
        self.delays.append(seconds)


class HostingerMirrorQuotaTests(unittest.TestCase):
    def check_case(self, repo, replies, expected, count, delays):
        seen = []
        timer = Timer()
        def verify(name):
            seen.append(name)
            value = replies[len(seen) - 1]
            if isinstance(value, Exception):
                raise value
            return value
        fn = load_retry(verify, timer)
        if isinstance(expected, Exception):
            with self.assertRaisesRegex(type(expected), str(expected)):
                fn(repo)
        else:
            self.assertEqual(fn(repo), expected)
        self.assertEqual(len(seen), count)
        self.assertEqual(timer.delays, delays)

    def test_success_no_retry(self):
        self.check_case("anthares-kwai-runner", ["PASS"], "PASS", 1, [])

    def test_transient_quota_one_retry(self):
        self.check_case("anthares-kwai-runner",
                        [RuntimeError("HOSTING_PROCESS_LIMIT"), "PASS"],
                        "PASS", 2, [4])

    def test_permanent_quota_stops_after_one_retry(self):
        self.check_case("anthares-kwai-runner",
                        [RuntimeError("HOSTING_PROCESS_LIMIT")] * 2,
                        RuntimeError("HOSTING_PROCESS_LIMIT"), 2, [4])

    def test_other_repo_quota_not_retried(self):
        self.check_case("anthares-wordpress",
                        [RuntimeError("HOSTING_PROCESS_LIMIT")],
                        RuntimeError("HOSTING_PROCESS_LIMIT"), 1, [])

    def test_other_error_not_retried(self):
        self.check_case("anthares-kwai-runner",
                        [RuntimeError("GIT_FAILED_128")],
                        RuntimeError("GIT_FAILED_128"), 1, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
