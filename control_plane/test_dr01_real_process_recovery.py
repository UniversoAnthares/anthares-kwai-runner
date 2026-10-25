"""DR-01: real subprocess loss and durable QA-only receipt reconciliation.

Runs ONLY in a disposable .cortes-iso03-qa-only sandbox, without any
external network, media, social accounts, Neon, credentials, or posting.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from qa_iso03_fenced_queue import QAFencedQueue, ScopeDenied


# A physically separate subprocess commits a lease, STARTED state and,
# in one scenario, a mock external receipt to a separate durable file.
# Its PID is killed by the test process before ledger acknowledgement.
CHILD = r"""
import json, os, pathlib, sys, time
from qa_iso03_fenced_queue import QAFencedQueue
root=pathlib.Path(sys.argv[1])
with_receipt=sys.argv[2]=='yes'
q=QAFencedQueue(root,'tiktok','lucasrosalem4')
claim=q.claim('original_qa_writer')
assert claim is not None
q.start(claim)
tmp=root/'claim.json.tmp'
with tmp.open('w') as f:
    os.chmod(tmp,0o600)
    json.dump(claim,f)
    f.flush();os.fsync(f.fileno())
os.replace(tmp,root/'claim.json')
if with_receipt:
    receipt={'remote_id':'mock_receipt_qa_0001','network':'tiktok','account':'lucasrosalem4'}
    tmp=root/'remote_receipt.json.tmp'
    with tmp.open('w') as f:
        json.dump(receipt,f)
        f.flush();os.fsync(f.fileno())
    os.replace(tmp,root/'remote_receipt.json')
print('READY_FOR_KILL',flush=True)
time.sleep(120)
"""


class RealLossFailoverQA(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dr01-real-kill-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / ".cortes-iso03-qa-only").write_text("qa-only\n", encoding="ascii")
        (self.root / "tiktok").mkdir()
        (self.root / "kwai").mkdir()
        self.tiktok = QAFencedQueue(self.root,"tiktok","lucasrosalem4")
        self.kwai = QAFencedQueue(self.root,"kwai","lucasrosalem")
        self.tiktok.enqueue("dr01_disposable_qa_event")

    @unittest.skipUnless(os.name == "posix", "Hosted POSIX kill test only")
    def crash_original_writer(self, with_receipt):
        start = time.monotonic()
        process = subprocess.Popen(
            [sys.executable, "-u", "-c", CHILD, str(self.root), "yes" if with_receipt else "no"],
            cwd=str(Path(__file__).resolve().parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            self.assertEqual(process.stdout.readline().strip(), "READY_FOR_KILL")
            self.assertIsNone(process.poll(), "Writer exited before controlled kill")
            process.kill()  # OS SIGKILL: not a mocked exception or a theoretical test
            process.wait(timeout=10)
            self.assertNotEqual(process.returncode, 0)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=10)
            process.stdout.close()
            process.stderr.close()
        recovery = QAFencedQueue(self.root, "tiktok", "lucasrosalem4")
        self.assertEqual(recovery.count_states(), {"started": 1})
        # Failover writer cannot claim a STARTED event, even with a live broker.
        self.assertIsNone(recovery.claim("replacement_qa_writer"))
        claim = json.loads((self.root / "claim.json").read_text(encoding="utf-8"))
        self.assertEqual(claim["network"], "tiktok")
        self.assertLess(time.monotonic() - start, 10.0, "Recovery exceeded QA RTO 10 seconds")
        return recovery, claim

    def test_kill_with_durable_mock_external_receipt_reconcile_once(self):
        recovery, claim = self.crash_original_writer(with_receipt=True)
        receipt = json.loads((self.root / "remote_receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["network"], "tiktok")
        self.assertEqual(receipt["account"], "lucasrosalem4")
        self.assertTrue(receipt["remote_id"].startswith("mock_receipt_qa_"))
        sha = hashlib.sha256((self.root / "remote_receipt.json").read_bytes()).hexdigest()
        recovery.confirm(claim, receipt["remote_id"])
        self.assertEqual(recovery.count_states(), {"confirmed": 1})
        self.assertEqual(recovery.count_effects(), 1)
        self.assertEqual(self.kwai.count_effects(), 0)
        # After another restart, the identical remote QA receipt is not replayable.
        restarted = QAFencedQueue(self.root, "tiktok", "lucasrosalem4")
        self.assertEqual(restarted.count_effects(), 1)
        with self.assertRaises(ScopeDenied):
            restarted.confirm(claim, receipt["remote_id"])
        self.assertEqual(
            hashlib.sha256((self.root / "remote_receipt.json").read_bytes()).hexdigest(),
            sha,
            "Mock external receipt SHA changed after failover",
        )
        self.assertIsNone(restarted.claim("late_qa_writer"))

    def test_kill_without_receipt_never_resubmits_or_crossposts(self):
        recovery, claim = self.crash_original_writer(with_receipt=False)
        self.assertFalse((self.root / "remote_receipt.json").exists())
        # No external proof => quarantine, never invent a confirmation.
        recovery.uncertain(claim)
        restarted = QAFencedQueue(self.root,"tiktok","lucasrosalem4")
        self.assertEqual(restarted.count_states(), {"uncertain": 1})
        self.assertEqual(restarted.count_effects(), 0)
        self.assertIsNone(restarted.claim("recovery_qa_writer"))
        self.assertEqual(self.kwai.count_effects(),0)
        with self.assertRaises(ScopeDenied):
            restarted.confirm(claim,"forbidden_replay_qa")
        self.assertEqual(restarted.count_effects(),0)


if __name__ == "__main__":
    unittest.main()
