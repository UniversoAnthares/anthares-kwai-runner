import tempfile
import unittest
from pathlib import Path
from anthares_publisher.publication_queue import (
    connect,enqueue,claim,heartbeat,mark_publication_started,fail_before_publish,
    mark_uncertain,confirm,recover_stale,queue_state,
)

class PublicationQueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.db=connect(str(Path(self.tmp.name)/'q.sqlite3'))
    def tearDown(self): self.db.close(); self.tmp.cleanup()

    def test_enqueue_is_idempotent(self):
        a=enqueue(self.db,'pub-1','kwai','@A',now=100)
        b=enqueue(self.db,'pub-1','kwai','a',now=101)
        self.assertEqual(a,b)

    def test_target_is_serialized_but_other_account_can_run(self):
        enqueue(self.db,'pub-1','kwai','a',now=100)
        enqueue(self.db,'pub-2','kwai','a',now=101)
        enqueue(self.db,'pub-3','kwai','b',now=102)
        first=claim(self.db,'w1',ttl=30,now=110)
        second=claim(self.db,'w2',ttl=30,now=110)
        self.assertEqual(first['account_id'],'a')
        self.assertEqual(second['account_id'],'b')

    def test_stale_pre_fence_lease_is_requeued_with_higher_generation(self):
        enqueue(self.db,'pub-1','tiktok','a',now=100)
        one=claim(self.db,'w1',ttl=10,now=100)
        self.assertEqual(recover_stale(self.db,111)['retry_safe_requeued'],1)
        two=claim(self.db,'w2',ttl=10,now=111)
        self.assertEqual(two['lease_generation'],one['lease_generation']+1)
        self.assertFalse(heartbeat(self.db,two['id'],'w1',one['lease_generation'],10,112))
        self.assertTrue(heartbeat(self.db,two['id'],'w2',two['lease_generation'],10,112))

    def test_stale_post_fence_lease_becomes_uncertain_and_blocks_target(self):
        enqueue(self.db,'pub-1','kwai','a',now=100)
        enqueue(self.db,'pub-2','kwai','a',now=101)
        job=claim(self.db,'w1',ttl=10,now=100)
        self.assertTrue(mark_publication_started(self.db,job['id'],'w1',job['lease_generation'],101))
        out=recover_stale(self.db,111)
        self.assertEqual(out['uncertain_quarantined'],1)
        self.assertIsNone(claim(self.db,'w2',ttl=10,now=111))
        self.assertTrue(confirm(self.db,job['id'],now=112))
        self.assertIsNotNone(claim(self.db,'w2',ttl=10,now=113))

    def test_failure_before_fence_is_retry_safe(self):
        enqueue(self.db,'pub-1','kwai','a',now=100)
        job=claim(self.db,'w1',ttl=30,now=101)
        self.assertTrue(fail_before_publish(self.db,job['id'],'w1',job['lease_generation'],'network before submit',102))
        self.assertEqual(queue_state(self.db)['queued'],1)

    def test_old_generation_cannot_cross_publication_fence(self):
        enqueue(self.db,'pub-1','kwai','a',now=100)
        old=claim(self.db,'w1',ttl=10,now=100)
        recover_stale(self.db,111)
        new=claim(self.db,'w2',ttl=10,now=111)
        self.assertFalse(mark_publication_started(self.db,new['id'],'w1',old['lease_generation'],112))
        self.assertTrue(mark_publication_started(self.db,new['id'],'w2',new['lease_generation'],112))
        self.assertTrue(mark_uncertain(self.db,new['id'],'w2',new['lease_generation'],'ambiguous',113))

if __name__=='__main__': unittest.main()
