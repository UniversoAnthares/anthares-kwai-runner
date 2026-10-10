import tempfile
import unittest
from pathlib import Path
from anthares_core.queue import connect, enqueue, claim, finish, heartbeat

class CoreQueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=connect(str(Path(self.tmp.name)/'tasks.db'))
    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()
    def test_fencing_and_idempotency(self):
        enqueue(self.db,'probe',{'target':'runner'},'fixed')
        enqueue(self.db,'probe',{'target':'runner'},'fixed')
        a=claim(self.db,'worker-a',120)
        self.assertEqual(a['id'],'fixed')
        self.assertIsNone(claim(self.db,'worker-b'))
        self.assertFalse(finish(self.db,'fixed','invalid',{'ok':True}))
        self.assertTrue(heartbeat(self.db,'fixed',a['token']))
        self.assertTrue(finish(self.db,'fixed',a['token'],{'ok':True}))
        self.assertFalse(finish(self.db,'fixed',a['token'],{'ok':True}))
        self.assertIsNone(claim(self.db,'worker-b'))
    def test_expired_lease_reclaimed_and_old_token_rejected(self):
        enqueue(self.db,'probe',{},'recover')
        a=claim(self.db,'worker-a',1)
        self.db.execute('UPDATE tasks SET lease_until=0 WHERE id=?',('recover',))
        b=claim(self.db,'worker-b',120)
        self.assertEqual(b['attempts'],2)
        self.assertNotEqual(a['token'],b['token'])
        self.assertFalse(finish(self.db,'recover',a['token'],{}))
        self.assertTrue(finish(self.db,'recover',b['token'],{'recovered':True}))

    def test_expired_irreversible_job_is_quarantined(self):
        enqueue(self.db,'kwai_publish',{'video':'opaque-id'},'post-1')
        first=claim(self.db,'runner-1',120)
        self.db.execute("UPDATE tasks SET lease_until=0 WHERE id='post-1'")
        self.assertIsNone(claim(self.db,'runner-2'))
        self.assertEqual(self.db.execute("SELECT status FROM tasks WHERE id='post-1'").fetchone()[0],'uncertain')
        self.assertFalse(finish(self.db,'post-1',first['token'],{'ok':True}))
    def test_expired_probe_retry_budget(self):
        enqueue(self.db,'probe',{},'bounded')
        for attempt in range(1,4):
            claimed=claim(self.db,'runner',120)
            self.assertEqual(claimed['attempts'],attempt)
            self.db.execute("UPDATE tasks SET lease_until=0 WHERE id='bounded'")
        self.assertIsNone(claim(self.db,'runner'))
        self.assertEqual(self.db.execute("SELECT status FROM tasks WHERE id='bounded'").fetchone()[0],'failed')

if __name__=='__main__':unittest.main()
