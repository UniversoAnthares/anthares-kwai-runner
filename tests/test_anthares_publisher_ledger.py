import tempfile
import unittest
from pathlib import Path
from anthares_publisher.ledger import connect,reserve,mark_attempt,fail,confirm

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

if __name__=='__main__':unittest.main()
