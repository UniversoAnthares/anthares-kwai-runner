import tempfile
import unittest
from pathlib import Path

from dedupe import Cut, CutLedger, overlap_ratio


H1 = "a" * 64
H2 = "b" * 64
H3 = "c" * 64


class DedupeTests(unittest.TestCase):
    def test_overlap_ratio(self):
        self.assertEqual(overlap_ratio(0, 100, 200, 300), 0.0)
        self.assertEqual(overlap_ratio(0, 100, 50, 100), 1.0)
        self.assertEqual(overlap_ratio(0, 100, 0, 100), 1.0)

    def test_reject_same_hash_or_overlapping_range(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ledger.json"
            ledger = CutLedger(path)
            first = Cut("live-1", 0, 10000, H1)
            ledger.reserve(first)
            self.assertFalse(ledger.eligible(Cut("live-2", 20000, 30000, H1)))
            self.assertFalse(ledger.eligible(Cut("live-1", 8500, 18500, H2)))
            self.assertTrue(ledger.eligible(Cut("live-1", 12000, 22000, H3)))

    def test_persists_across_processes(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ledger.json"
            CutLedger(path).reserve(Cut("live-9", 1000, 5000, H1))
            second = CutLedger(path)
            self.assertTrue(second.seen_hash(H1))
            self.assertTrue(second.overlaps("live-9", 2000, 4500))


if __name__ == "__main__":
    unittest.main()
