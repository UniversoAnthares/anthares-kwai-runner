import importlib.util
import os
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("kwai_up_job", ROOT / "kwai_up_job.py")
kj = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = kj
SPEC.loader.exec_module(kj)
CASE = int(os.environ.get("KWAI_UP_CASE", "1"))


def ident(job, source, start, end, sha):
    return kj.Identity(job, source, start, end, pathlib.Path("/tmp/fake.mp4"), sha)


class TestLedger(unittest.TestCase):
    def make(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        return kj.Ledger(pathlib.Path(td.name) / "ledger.sqlite3")

    def test_same_hash_is_rejected(self):
        ledger = self.make()
        sha = (f"{CASE:02x}" * 32)[:64]
        ledger.reserve(ident("a", "live", 0, 50000, sha))
        with self.assertRaises(kj.JobError):
            ledger.reserve(ident("b", "other", 100000, 150000, sha))

    def test_overlap_same_source_is_rejected(self):
        ledger = self.make()
        ledger.reserve(ident("a", "live", 100000, 160000, "a" * 64))
        shift = CASE % 20 + 1
        with self.assertRaises(kj.JobError):
            ledger.reserve(ident("b", "live", 100000 + shift * 1000, 190000, "b" * 64))

    def test_adjacent_interval_is_allowed(self):
        ledger = self.make()
        ledger.reserve(ident("a", "live", 100000, 160000, "a" * 64))
        ledger.reserve(ident("b", "live", 160000, 220000, "b" * 64))
        self.assertEqual(ledger.get("b")["state"], "RESERVED")

    def test_same_interval_different_source_is_allowed(self):
        ledger = self.make()
        ledger.reserve(ident("a", "live-a", 100000, 160000, "a" * 64))
        ledger.reserve(ident("b", "live-b", 100000, 160000, "b" * 64))
        self.assertEqual(ledger.get("b")["state"], "RESERVED")

    def test_uncertain_remains_deduped(self):
        ledger = self.make()
        ledger.reserve(ident("a", "live", 100000, 160000, "a" * 64))
        ledger.state("a", "UNCERTAIN", publish_requested=True)
        row = ledger.get("a")
        self.assertEqual(row["state"], "UNCERTAIN")
        self.assertEqual(row["publish_requested"], 1)
        with self.assertRaises(kj.JobError):
            ledger.reserve(ident("b", "live", 120000, 170000, "b" * 64))

    def test_verified_remains_deduped(self):
        ledger = self.make()
        ledger.reserve(ident("a", "live", 100000, 160000, "a" * 64))
        ledger.state("a", "VERIFIED", publish_requested=True)
        with self.assertRaises(kj.JobError):
            ledger.reserve(ident("b", "live", 100000, 160000, "b" * 64))

    def test_duplicate_job_id_is_rejected(self):
        ledger = self.make()
        ledger.reserve(ident("same", "live-a", 0, 50000, "a" * 64))
        with self.assertRaises(kj.JobError):
            ledger.reserve(ident("same", "live-b", 60000, 110000, "b" * 64))


if __name__ == "__main__":
    unittest.main()
