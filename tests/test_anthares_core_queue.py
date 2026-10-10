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

if __name__=='__main__':unittest.main()
