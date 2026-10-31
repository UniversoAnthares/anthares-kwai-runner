"""Regression tests for ARA Durable Object read quota (SQLite, offline)."""
from pathlib import Path
import re
import sqlite3
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "cloudflare-ara-backup/src/index.js"
EXPIRED = ("SELECT id,type,status,expires_at,lease_until FROM ara_jobs "
           "WHERE device_id=? AND status IN ('queued','leased','uncertain') AND expires_at<=?")
LEASE = ("SELECT id,type,status,expires_at,lease_until FROM ara_jobs "
         "WHERE device_id=? AND status='leased' AND lease_until<=? AND expires_at>?")
COUNTS = ("SELECT status,COUNT(*) AS n FROM ara_jobs "
          "WHERE device_id=? AND status IN ('queued','leased','uncertain') GROUP BY status")
PICK = ("SELECT * FROM ara_jobs WHERE device_id=? AND status='queued' "
        "AND expires_at>? ORDER BY created_at LIMIT 1")


class DurableObjectReadQuotaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        tick = chr(96)
        match = re.search(r"this\.sql\.exec\(\s*" + tick + r"(.*?)" + tick + r"\s*\);", cls.source, re.S)
        if not match:
            raise AssertionError("Durable Object SQL schema missing")
        cls.schema = match.group(1)

    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript(self.schema)
        self.now = 1000000
        now = self.now
        rows = [
            (f"historic-{n}", "workstation", "ping", "{}", 30, n, now - 10,
             ("done", "failed", "expired")[n % 3], None)
            for n in range(12000)
        ]
        rows += [
            ("q-expired", "workstation", "ping", "{}", 30, 20000, now - 1, "queued", None),
            ("q-live", "workstation", "ping", "{}", 30, 20001, now + 500, "queued", None),
            ("l-expired", "workstation", "ping", "{}", 30, 20002, now - 1, "leased", now - 10),
            ("l-lease-expired", "workstation", "ping", "{}", 30, 20003, now + 500, "leased", now - 10),
            ("l-live", "workstation", "ping", "{}", 30, 20004, now + 500, "leased", now + 200),
            ("u-expired", "workstation", "ping", "{}", 30, 20005, now - 1, "uncertain", None),
            ("u-live", "workstation", "ping", "{}", 30, 20006, now + 500, "uncertain", None),
            ("other", "different-device", "ping", "{}", 30, 20007, now + 500, "queued", None),
        ]
        self.db.executemany(
            "INSERT INTO ara_jobs(id,device_id,type,args,timeout_seconds,"
            "created_at,expires_at,status,lease_until) VALUES(?,?,?,?,?,?,?,?,?)", rows
        )

    def tearDown(self):
        self.db.close()

    def assert_index_plan(self, sql, params, index_name):
        details = " ".join(row[3] for row in self.db.execute("EXPLAIN QUERY PLAN " + sql, params))
        self.assertIn(index_name, details)
        self.assertNotIn("SCAN ara_jobs", details)

    def test_source_uses_bounded_queries(self):
        normalized = " ".join(self.source.split())
        for sql in (EXPIRED, LEASE, COUNTS):
            self.assertIn(sql, normalized)
        self.assertNotIn("SUM(CASE WHEN status=", self.source)
        self.assertNotIn("DROP INDEX IF EXISTS ara_jobs_pick;", self.source)

    def test_active_counts_exclude_historical_rows(self):
        self.assert_index_plan(COUNTS, ("workstation",), "ara_jobs_active_counts")
        counts = {row["status"]: row["n"] for row in self.db.execute(COUNTS, ("workstation",))}
        self.assertEqual(counts, {"queued": 2, "leased": 3, "uncertain": 2})

    def test_reaper_only_reads_due_rows(self):
        self.assert_index_plan(EXPIRED, ("workstation", self.now), "ara_jobs_active_expiry")
        self.assert_index_plan(LEASE, ("workstation", self.now, self.now), "ara_jobs_active_lease")
        expired = {row["id"] for row in self.db.execute(EXPIRED, ("workstation", self.now))}
        leases = {row["id"] for row in self.db.execute(LEASE, ("workstation", self.now, self.now))}
        self.assertEqual(expired, {"q-expired", "l-expired", "u-expired"})
        self.assertEqual(leases, {"l-lease-expired"})

    def test_stateful_deployment_requires_explicit_dispatch(self):
        workflow = (SOURCE.parents[1] / ".github/workflows/trigger-cloudflare-ara-backup-deploy.yml").read_text(encoding="utf-8")
        self.assertIn("  workflow_dispatch:", workflow)
        self.assertNotIn("  push:", workflow)

    def test_lease_pick_uses_created_order_index(self):
        self.assert_index_plan(PICK, ("workstation", self.now), "ara_jobs_pick")
        row = self.db.execute(PICK, ("workstation", self.now)).fetchone()
        self.assertEqual(row["id"], "q-live")


if __name__ == "__main__":
    unittest.main()
