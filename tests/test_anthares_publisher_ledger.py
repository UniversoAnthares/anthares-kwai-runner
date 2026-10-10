import tempfile
import unittest
from pathlib import Path
from anthares_publisher.ledger import connect,reserve,mark_attempt,fail,confirm
from anthares_publisher.state_store import export_state,import_state

class PublisherLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.db=connect(str(Path(self.tmp.name)/'p.sqlite3'))
    def tearDown(self):
        self.db.close();self.tmp.cleanup()
    def test_dedupes_same_source_timecode_target(self):
        a=reserve(self.db,'live-1',1000,9000,'kwai','lucasrosalem','a'*64)
        b=reserve(self.db,'live-1',1000,9000,'kwai','lucasrosalem','a'*64)
        self.assertEqual(a['id'],b['id'])
        self.assertEqual(self.db.execute('SELECT count(*) FROM publications').fetchone()[0],1)
    def test_rejects_hash_change_for_same_slot(self):
        reserve(self.db,'live-1',1000,9000,'kwai','lucasrosalem','a'*64)
        with self.assertRaises(ValueError):
            reserve(self.db,'live-1',1000,9000,'kwai','lucasrosalem','b'*64)
    def test_requires_external_evidence_before_published(self):
        p=reserve(self.db,'live-2',0,5000,'kwai','lucasrosalem','c'*64)
        self.assertTrue(mark_attempt(self.db,p['id']))
        with self.assertRaises(ValueError): confirm(self.db,p['id'],'','')
        self.assertTrue(confirm(self.db,p['id'],'kwai-video-1','https://www.kwai.com/v/kwai-video-1'))
        row=self.db.execute('SELECT status,external_id,public_url FROM publications WHERE id=?',(p['id'],)).fetchone()
        self.assertEqual(row[0],'published')
        self.assertEqual(row[1],'kwai-video-1')
    def test_retry_never_marks_published(self):
        p=reserve(self.db,'live-3',0,5000,'kwai','lucasrosalem','d'*64)
        self.assertTrue(mark_attempt(self.db,p['id']))
        self.assertTrue(fail(self.db,p['id'],True))
        self.assertEqual(self.db.execute('SELECT status FROM publications WHERE id=?',(p['id'],)).fetchone()[0],'retry')
    def test_unknown_outcome_is_quarantined_and_not_retried(self):
        p=reserve(self.db,'live-uncertain',0,5000,'kwai','lucasrosalem','f'*64)
        self.assertTrue(mark_attempt(self.db,p['id']))
        self.assertTrue(fail(self.db,p['id']))
        self.assertEqual(self.db.execute('SELECT status FROM publications WHERE id=?',(p['id'],)).fetchone()[0],'uncertain')
        self.assertFalse(mark_attempt(self.db,p['id']))
        self.assertFalse(confirm(self.db,p['id'],'fake','https://www.kwai.com/v/fake'))
    def test_overlapping_timecode_rejected_even_with_different_hash(self):
        reserve(self.db,'same-live',1000,9000,'kwai','lucasrosalem','1'*64)
        with self.assertRaisesRegex(ValueError,'overlapping'):
            reserve(self.db,'same-live',8500,14000,'kwai','lucasrosalem','2'*64)
        self.assertEqual(self.db.execute('SELECT count(*) FROM publications').fetchone()[0],1)
    def test_duplicate_content_rejected_across_different_lives(self):
        reserve(self.db,'live-A',0,1000,'kwai','lucasrosalem','3'*64)
        with self.assertRaisesRegex(ValueError,'identical video'):
            reserve(self.db,'live-B',0,1000,'kwai','lucasrosalem','3'*64)
    def test_same_clip_can_target_other_platform(self):
        reserve(self.db,'live-A',0,1000,'kwai','lucasrosalem','4'*64)
        reserve(self.db,'live-A',0,1000,'tiktok','lucasrosalem','4'*64)
        self.assertEqual(self.db.execute('SELECT count(*) FROM publications').fetchone()[0],2)
    def test_explicit_pre_submit_failure_can_be_retried(self):
        p=reserve(self.db,'live-pre-submit',0,5000,'kwai','lucasrosalem','5'*64)
        self.assertTrue(mark_attempt(self.db,p['id']))
        self.assertTrue(fail(self.db,p['id'],retry=True))
        self.assertTrue(mark_attempt(self.db,p['id']))
    def test_bad_hash_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'hex digest'):
            reserve(self.db,'live-X',0,1000,'kwai','lucasrosalem','not-a-digest')
    def test_durable_state_round_trip_preserves_evidence(self):
        p=reserve(self.db,'live-4',100,6000,'kwai','lucasrosalem','e'*64)
        self.assertTrue(mark_attempt(self.db,p['id']))
        self.assertTrue(confirm(self.db,p['id'],'ext-4','https://www.kwai.com/v/ext-4'))
        state=str(Path(self.tmp.name)/'publisher.json');restored=str(Path(self.tmp.name)/'restored.sqlite3')
        self.assertEqual(export_state(self.db.execute('PRAGMA database_list').fetchone()[2],state),1)
        self.assertEqual(import_state(state,restored),1)
        other=connect(restored);row=other.execute('SELECT status,external_id,public_url FROM publications WHERE id=?',(p['id'],)).fetchone();other.close()
        self.assertEqual(row,('published','ext-4','https://www.kwai.com/v/ext-4'))

if __name__=='__main__':unittest.main()
