import tempfile
import unittest
from pathlib import Path
from anthares_publisher.global_dedupe import (
    connect,reserve,conflicts,mark_publication_started,mark_uncertain,
    confirm,reconcile_absent,can_retry,snapshot,
)

class GlobalDedupeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.db=connect(str(Path(self.tmp.name)/'d.sqlite3'))
    def tearDown(self): self.db.close(); self.tmp.cleanup()

    def test_same_target_blocks_exact_hash(self):
        one=reserve(self.db,'source-1',0,60000,'1'*64,'kwai','a',now=100)
        self.assertTrue(one['created'])
        two=reserve(self.db,'source-2',0,60000,'1'*64,'kwai','a',now=101)
        self.assertFalse(two['created']);self.assertEqual(two['reason'],'content_hash')

    def test_same_target_blocks_positive_temporal_overlap(self):
        reserve(self.db,'source-1',120000,180000,'1'*64,'kwai','a',now=100)
        conflict=reserve(self.db,'source-1',150000,210000,'2'*64,'kwai','a',now=101)
        self.assertFalse(conflict['created']);self.assertEqual(conflict['reason'],'temporal_overlap')
        touching=reserve(self.db,'source-1',180000,240000,'3'*64,'kwai','a',now=102)
        self.assertTrue(touching['created'])

    def test_different_destination_is_independent(self):
        reserve(self.db,'source-1',0,60000,'1'*64,'kwai','a',now=100)
        self.assertTrue(reserve(self.db,'source-1',0,60000,'1'*64,'tiktok','a',now=101)['created'])
        self.assertTrue(reserve(self.db,'source-1',0,60000,'1'*64,'kwai','b',now=102)['created'])

    def test_uncertain_never_becomes_retryable_without_reconciliation(self):
        row=reserve(self.db,'source-1',0,60000,'1'*64,'kwai','a',now=100)
        self.assertTrue(mark_publication_started(self.db,row['id'],101))
        self.assertTrue(mark_uncertain(self.db,row['id'],'timeout after submit',102))
        self.assertFalse(can_retry(self.db,row['id']))
        self.assertFalse(reconcile_absent(self.db,row['id'],False,'not checked',103))
        self.assertFalse(can_retry(self.db,row['id']))
        self.assertTrue(reconcile_absent(self.db,row['id'],True,'profile inventory checked',104))
        self.assertTrue(can_retry(self.db,row['id']))

    def test_uncertain_can_be_reconciled_to_confirmed(self):
        row=reserve(self.db,'source-1',0,60000,'1'*64,'kwai','a',now=100)
        mark_publication_started(self.db,row['id'],101);mark_uncertain(self.db,row['id'],'runner lost',102)
        self.assertTrue(confirm(self.db,row['id'],'remote-123',103))
        state=snapshot(self.db,'kwai','a')[0]
        self.assertEqual(state['state'],'confirmed');self.assertEqual(state['remote_id'],'remote-123')

    def test_reserved_and_uncertain_are_both_dedupe_active(self):
        row=reserve(self.db,'source-1',0,60000,'1'*64,'kwai','a',now=100)
        self.assertTrue(conflicts(self.db,'source-1',1000,59000,'9'*64,'kwai','a')['conflict'])
        mark_publication_started(self.db,row['id'],101);mark_uncertain(self.db,row['id'],'ambiguous',102)
        self.assertTrue(conflicts(self.db,'source-1',1000,59000,'9'*64,'kwai','a')['conflict'])

if __name__=='__main__': unittest.main()
