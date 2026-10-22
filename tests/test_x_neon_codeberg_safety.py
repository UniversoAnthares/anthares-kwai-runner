"""Offline safety-contract tests for Codeberg X primary and Neon ledger switchover."""
import ast
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.parse import urlparse

SOURCE = Path(__file__).resolve().parents[1] / "tools" / "x_github_anthares_browser_publisher.py"


def functions():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    defs = [n for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name in {"durable", "_neon_durable"}]
    assert len(defs) == 2
    ns = {"os": os, "urlparse": urlparse, "ACCOUNT": "lucasyahn"}
    exec(compile(ast.Module(body=defs, type_ignores=[]), str(SOURCE), "exec"), ns)
    return ns


class TestCodebergLedgerSafety(unittest.TestCase):
    def setUp(self):
        self.ns = functions()
        self.key = "x-long-20261022-test-safe"

    def test_codeberg_cannot_reuse_northflank_ledger(self):
        with patch.dict(os.environ, {"X_CLOUD_PROVIDER": "codeberg", "ARA_SHARED": "dummy"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "X_CODEBERG_NORTHFLANK_LEDGER_FORBIDDEN"):
                self.ns["durable"]("/post-status?idempotency_key=" + self.key)

    def test_neon_requires_verified_migration(self):
        env = {"X_LEDGER_BACKEND": "neon", "X_LEDGER_DATABASE_URL": "postgresql://a@db.neon.tech/d"}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(RuntimeError, "X_NEON_LEDGER_MIGRATION_NOT_VERIFIED"):
                self.ns["durable"]("/claim-local", {"account": "lucasyahn", "idempotency_key": self.key})

    def test_neon_rejects_non_neon_database_host(self):
        env = {"X_LEDGER_BACKEND": "neon", "X_LEDGER_DATABASE_URL": "postgresql://a@northflank.com/db",
               "X_LEDGER_MIGRATION_VERIFIED": "1"}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(RuntimeError, "X_NEON_DATABASE_URL_REQUIRED"):
                self.ns["durable"]("/post-status?idempotency_key=" + self.key)

    def test_confirmation_needs_verified_video_and_caption(self):
        env = {"X_LEDGER_BACKEND": "neon", "X_LEDGER_DATABASE_URL": "postgresql://a@db.neon.tech/d",
               "X_LEDGER_MIGRATION_VERIFIED": "1"}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(RuntimeError, "X_NEON_CONFIRM_EVIDENCE_REQUIRED"):
                self.ns["durable"]("/confirm-local", {
                    "account": "lucasyahn", "idempotency_key": self.key, "video_verified": False,
                    "caption_verified": True, "post_url": "https://x.com/lucasyahn/status/12345"})

    def test_neon_claim_delegates_to_atomic_database_ledger(self):
        from tools import x_durable_ledger as ledger
        env = {"X_LEDGER_BACKEND": "neon", "X_LEDGER_DATABASE_URL": "postgresql://a@db.neon.tech/d",
               "X_LEDGER_MIGRATION_VERIFIED": "1"}
        with patch.dict(os.environ, env, clear=True), patch.object(ledger, "begin") as begin:
            result = self.ns["durable"]("/claim-local", {
                "account": "lucasyahn", "idempotency_key": self.key})
            self.assertTrue(result["claimed"])
            begin.assert_called_once_with(self.key)

    def test_duplicate_claim_refused_without_retry(self):
        from tools import x_durable_ledger as ledger
        env = {"X_LEDGER_BACKEND": "neon", "X_LEDGER_DATABASE_URL": "postgresql://a@db.neon.tech/d",
               "X_LEDGER_MIGRATION_VERIFIED": "1"}
        with patch.dict(os.environ, env, clear=True), patch.object(
                ledger, "begin", side_effect=ledger.AlreadyStarted("previous")):
            with self.assertRaisesRegex(RuntimeError, "X_PREVIOUS_SUBMISSION_RECONCILE"):
                self.ns["durable"]("/claim-local", {
                    "account": "lucasyahn", "idempotency_key": self.key})


if __name__ == "__main__":
    unittest.main()
