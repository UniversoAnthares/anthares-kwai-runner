"""ISO-03 R07.6: multiprocess writer contention on an isolated SQLite QA broker.

Independent subprocesses use the same QA-only broker. Never access the
production database, publication accounts or external network.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from qa_iso03_fenced_queue import QAFencedQueue, ScopeDenied, kwai_fanout_shadow

CHILD = r"""
import json, pathlib, sys, time
from qa_iso03_fenced_queue import QAFencedQueue
root=pathlib.Path(sys.argv[1]); worker=sys.argv[2]
(root/'ready'/worker).write_text('ready')
deadline=time.monotonic()+10
while not (root/'go').exists():
    if time.monotonic()>deadline:
        raise RuntimeError('qa barrier timeout')
    time.sleep(.003)
q=QAFencedQueue(root,'tiktok','lucasrosalem4')
claim=q.claim(worker)
if claim is None:
    print(json.dumps({'worker':worker,'result':'lost'}),flush=True)
else:
    q.start(claim)
    q.confirm(claim,'qa_remote_'+worker)
    print(json.dumps({'worker':worker,'result':'won'}),flush=True)
"""

class MultiProcessFencingQA(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='r07-iso03-multiprocess-')
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/'.cortes-iso03-qa-only').write_text('qa-only\n')
        for network in ('tiktok','kwai'):
            (self.root/network).mkdir()
        (self.root/'ready').mkdir()
        self.tiktok=QAFencedQueue(self.root,'tiktok','lucasrosalem4')
        self.kwai=QAFencedQueue(self.root,'kwai','lucasrosalem')

    def test_eight_rounds_six_real_processes_one_effect_each(self):
        rounds=8
        for index in range(rounds):
            self.tiktok.enqueue('qa_multiprocess_clip_'+str(index))
            gate=self.root/'go'
            gate.unlink(missing_ok=True)
            for file in (self.root/'ready').iterdir(): file.unlink()
            procs=[]
            try:
                for candidate in range(6):
                    worker='w'+str(index)+'_'+str(candidate)
                    procs.append(subprocess.Popen(
                        [sys.executable,'-B','-u','-c',CHILD,str(self.root),worker],
                        cwd=str(Path(__file__).resolve().parent),
                        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True))
                deadline=time.monotonic()+12
                while len(list((self.root/'ready').iterdir())) < 6:
                    self.assertLess(time.monotonic(),deadline,'not all subprocesses ready')
                    time.sleep(.005)
                gate.write_text('go')
                responses=[]
                for p in procs:
                    stdout,stderr=p.communicate(timeout=16)
                    self.assertEqual(p.returncode,0,(stdout,stderr))
                    responses.append(json.loads(stdout.strip()))
                self.assertEqual(sum(r['result']=='won' for r in responses),1,responses)
                self.assertEqual(sum(r['result']=='lost' for r in responses),5,responses)
                self.assertEqual(self.tiktok.count_effects(),index+1)
                self.assertEqual(self.kwai.count_effects(),0)
            finally:
                for p in procs:
                    if p.poll() is None: p.kill()
                    p.communicate(timeout=5)
        self.assertEqual(self.tiktok.count_states(),{'confirmed':8})
        self.assertEqual(self.kwai.count_states(),{})
        self.assertIsNone(self.tiktok.claim('late_writer'))

    def test_uncertain_replay_and_cross_scope_denied(self):
        self.tiktok.enqueue('qa_uncertain_unique')
        claim=self.tiktok.claim('qa_owner')
        self.assertIsNotNone(claim)
        self.tiktok.start(claim)
        self.tiktok.uncertain(claim)
        self.assertIsNone(QAFencedQueue(self.root,'tiktok','lucasrosalem4').claim('other'))
        with self.assertRaises(ScopeDenied):
            self.tiktok.confirm(claim,'qa_unverified')
        self.assertEqual(self.tiktok.count_effects(),0)
        self.kwai.enqueue('qa_kwai_unique')
        foreign=self.kwai.claim('kwai_writer')
        with self.assertRaises(ScopeDenied):
            self.tiktok.start(foreign)
        self.assertEqual(self.kwai.count_effects(),0)

    def test_kwai_shadow_is_only_non_executable_intent(self):
        s={'target_key':'kwai:lucasrosalem','segment_key':'qa_shadow_001','status':'queued'}
        output=kwai_fanout_shadow(s,trusted_controller=True)
        self.assertEqual(len(output['intents']),4)
        self.assertFalse(output['database_modified'] or output['cutover_authorized'])
        self.assertTrue(all(not r['publish_authorized'] and not r['enqueue_authorized'] for r in output['intents']))
        self.assertEqual(self.tiktok.count_states(),{})
        self.assertEqual(self.kwai.count_states(),{})

if __name__=='__main__':
    unittest.main()
