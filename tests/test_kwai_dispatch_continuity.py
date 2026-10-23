#!/usr/bin/env python3
"""Static regression gates only; never publishes or changes a queue."""
import ast
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return (ROOT / name).read_text(encoding="utf-8-sig")


class KwaiDispatchContinuityTests(unittest.TestCase):
    def test_neon_client_never_inherits_cloudflare_base(self):
        content = read("tools/cortes_neon_queue_client.py")
        ast.parse(content)
        self.assertIn("https://anthares-remote-primary.vercel.app/api/cortes-queue", content)
        self.assertNotIn("os.getenv('ANTHARES_CONTROL_URL'", content)

    def test_android_daemon_all_job_operations_fenced_by_neon(self):
        content = read("tools/kwai_physical_queue_daemon.py")
        tree = ast.parse(content)
        f = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                 and n.name == "signed_post")
        source = ast.get_source_segment(content, f)
        self.assertIn("path.startswith('/job/')", source)
        self.assertIn("signed_legacy_queue_call(path,payload)", source)
        self.assertNotIn("CORTES_QUEUE_BACKEND", source)

    def test_recovery_scripts_do_not_contain_interactive_task_artifacts(self):
        paths = (
            "ops/windows/cortes-kwai-autoheal.py",
            "ops/windows/cortes-kwai-refill-fallback.ps1",
            "ops/windows/cortes-kwai-qa-p0-watchdog.ps1",
        )
        for path in paths:
            with self.subTest(path=path):
                src = read(path)
                self.assertIsNone(re.search(r"(?m)^\[task:[a-f0-9]+\]", src))
                if path.endswith(".py"):
                    ast.parse(src)
                else:
                    self.assertTrue(src.startswith("$ErrorActionPreference='Stop'"))

    def test_independent_watchdog_cannot_publish_or_remove_a_security_hold(self):
        source = read("ops/windows/cortes-kwai-continuity-watchdog.ps1")
        self.assertIn("Get-CimInstance Win32_Process", source)
        self.assertIn("Start-ScheduledTask -TaskName $publisherTask", source)
        self.assertIn("if(Test-Path -LiteralPath $pause)", source)
        self.assertIn("HOLD_PAUSE_NOT_AUTHORIZED_FOR_RELEASE", source)
        for unsafe in ("Stop-Process", "taskkill", "Remove-Item $pause", "/job/lease"):
            self.assertNotIn(unsafe, source)
        installer = read("ops/windows/install-cortes-kwai-continuity-watchdog.ps1")
        self.assertIn("/SC MINUTE /MO 2", installer)
        self.assertIn("-WindowStyle Hidden", installer)
        self.assertIn("/RU SYSTEM", installer)


if __name__ == "__main__":
    unittest.main()
