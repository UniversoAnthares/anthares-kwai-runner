import tempfile
import unittest
from pathlib import Path
from anthares_publisher.ledger import connect,reserve,mark_attempt,confirm

class EvidenceGateTests(unittest.TestCase):
    def test_rejects_foreign_publication_url(self):
        with tempfile.TemporaryDirectory() as directory:
            db=connect(str(Path(directory)/'publisher.sqlite3'))
            job=reserve(db,'source-1',0,1000,'kwai','lucasrosalem','a'*64)
            self.assertTrue(mark_attempt(db,job['id']))
            with self.assertRaises(ValueError):
                confirm(db,job['id'],'fake-id','https://example.org/not-a-video')
            status=db.execute('SELECT status FROM publications WHERE id=?',(job['id'],)).fetchone()[0]
            self.assertEqual(status,'publishing')
            db.close()

if __name__=='__main__': unittest.main()
