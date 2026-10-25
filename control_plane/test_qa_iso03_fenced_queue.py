"""Real SQLite transactions and independent POSIX UIDs in disposable QA."""
import concurrent.futures
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

from qa_iso03_fenced_queue import QAFencedQueue, ScopeDenied, kwai_fanout_shadow


class Iso03QA(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="cortes-r076-iso03-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / ".cortes-iso03-qa-only").write_text("qa-only\n")
        for network in ("tiktok", "kwai"):
            (self.root / network).mkdir()
        self.tiktok = QAFencedQueue(self.root, "tiktok", "lucasrosalem4")
        self.kwai = QAFencedQueue(self.root, "kwai", "lucasrosalem")

    def test_real_concurrent_contenders_produce_one_effect(self):
        self.tiktok.enqueue("synthetic_tiktok_qa_clip")
        barrier = threading.Barrier(2)

        def compete(worker):
            broker = QAFencedQueue(self.root, "tiktok", "lucasrosalem4")
            barrier.wait(timeout=15)
            return broker.claim(worker)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            claimed = list(pool.map(compete, ("worker_a", "worker_b")))
        winners = [c for c in claimed if c]
        self.assertEqual(len(winners), 1, claimed)
        self.assertEqual(self.tiktok.count_states(), {"leased": 1})
        winner = winners[0]
        self.tiktok.start(winner)
        self.tiktok.confirm(winner, "synthetic_remote_qa_1")
        self.assertEqual(self.tiktok.count_effects(), 1)
        self.assertEqual(self.tiktok.count_states(), {"confirmed": 1})
        with self.assertRaises(ScopeDenied):
            self.tiktok.confirm(winner, "synthetic_remote_qa_2")
        self.assertEqual(self.tiktok.enqueue("synthetic_tiktok_qa_clip"), winner["id"])
        self.assertEqual(self.tiktok.count_effects(), 1)
        self.assertEqual(self.kwai.count_effects(), 0)

    def test_kwai_claim_cannot_start_tiktok(self):
        self.kwai.enqueue("synthetic_kwai_qa_clip")
        self.tiktok.enqueue("synthetic_tiktok_qa_clip")
        foreign = self.kwai.claim("kwai_worker")
        with self.assertRaisesRegex(ScopeDenied, "foreign_network_claim_denied"):
            self.tiktok.start(foreign)
        self.assertEqual(self.tiktok.count_states(), {"queued": 1})
        self.assertEqual(self.tiktok.count_effects(), 0)

    def test_uncertain_never_requeues(self):
        self.tiktok.enqueue("synthetic_uncertain_qa")
        claim = self.tiktok.claim("worker_a")
        self.tiktok.start(claim)
        self.tiktok.uncertain(claim)
        self.assertIsNone(self.tiktok.claim("worker_b"))
        self.assertEqual(self.tiktok.count_states(), {"uncertain": 1})
        self.assertEqual(self.tiktok.count_effects(), 0)

    def test_stale_generation_and_forged_token_denied(self):
        self.tiktok.enqueue("synthetic_fence_qa")
        claim = self.tiktok.claim("worker_a")
        invalids = (
            {**claim, "generation": claim["generation"] + 1},
            {**claim, "token": "c" * 64},
            {**claim, "network": "kwai"},
        )
        for invalid in invalids:
            with self.assertRaises(ScopeDenied):
                self.tiktok.start(invalid)
        self.assertEqual(self.tiktok.count_states(), {"leased": 1})

    def test_kwai_fanout_is_only_shadow_plan(self):
        source = {"target_key": "kwai:lucasrosalem",
                  "segment_key": "qa_clip_001", "status": "queued"}
        first = kwai_fanout_shadow(source, trusted_controller=True)
        second = kwai_fanout_shadow(source, trusted_controller=True)
        self.assertEqual(first, second)
        self.assertEqual(len(first["intents"]), 4)
        self.assertFalse(first["database_modified"])
        self.assertFalse(first["cutover_authorized"])
        self.assertTrue(all(not row["enqueue_authorized"] and not row["publish_authorized"]
                            for row in first["intents"]))
        self.assertEqual(self.kwai.count_states(), {})
        self.assertEqual(self.tiktok.count_states(), {})

    def test_qa_marker_is_mandatory(self):
        (self.root / ".cortes-iso03-qa-only").unlink()
        with self.assertRaisesRegex(ScopeDenied, "not_qa_environment"):
            QAFencedQueue(self.root, "tiktok", "lucasrosalem4")

    @unittest.skipUnless(os.name == "posix" and hasattr(os, "geteuid")
                         and os.geteuid() == 0,
                         "POSIX OS-identity denial requires isolated root QA runner")
    def test_real_distinct_os_uids_deny_other_network_state(self):
        # No users or tokens are created on any production machine.
        self.root.chmod(0o755)
        (self.root / ".cortes-iso03-qa-only").chmod(0o644)
        owned = (("kwai", 61071), ("tiktok", 61072))
        for network, uid in owned:
            directory = self.root / network
            os.chown(directory, uid, uid)
            directory.chmod(0o700)
            for qa_file in directory.iterdir():
                os.chown(qa_file, uid, uid)
                qa_file.chmod(0o600)
        child_code = """import sys
sys.path.insert(0,sys.argv[1])
from qa_iso03_fenced_queue import QAFencedQueue
try:
    q=QAFencedQueue(sys.argv[2],sys.argv[3],sys.argv[4])
    q.enqueue('qa_own_'+sys.argv[3])
    print('ALLOW')
except (PermissionError,OSError) as e:
    print('DENY_OS_PERMISSION:'+type(e).__name__)
"""
        for network, uid in owned:
            other = "kwai" if network == "tiktok" else "tiktok"

            def run(target):
                return subprocess.run(
                    [sys.executable, "-c", child_code,
                     str(Path(__file__).resolve().parent), str(self.root), target,
                     "lucasrosalem" if target == "kwai" else "lucasrosalem4"],
                    text=True, capture_output=True, timeout=15,
                    preexec_fn=lambda: os.setuid(uid))

            allowed = run(network)
            self.assertEqual(allowed.returncode, 0, (allowed.stdout, allowed.stderr))
            self.assertIn("ALLOW", allowed.stdout)
            denied = run(other)
            self.assertEqual(denied.returncode, 0, (denied.stdout, denied.stderr))
            self.assertIn("DENY_OS_PERMISSION", denied.stdout)


if __name__ == "__main__":
    unittest.main()
