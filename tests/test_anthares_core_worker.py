import tempfile
import unittest
from pathlib import Path
from anthares_core.queue import connect,enqueue
from anthares_core.worker import run

class WorkerTests(unittest.TestCase):
    def test_allowlisted_probe_completes(self):
        with tempfile.TemporaryDirectory() as d:
            dbp=str(Path(d)/'core.sqlite3')
            db=connect(dbp);enqueue(db,'probe',{'target':'qa'},'p1');db.close()
            out=run(dbp,'qa-worker')
            self.assertEqual(out[0]['id'],'p1')
            db=connect(dbp);row=db.execute("SELECT status,result FROM tasks WHERE id='p1'").fetchone();db.close()
            self.assertEqual(row[0],'done')
            self.assertIn('"ok": true',row[1])
    def test_unknown_kind_is_failed_not_executed(self):
        with tempfile.TemporaryDirectory() as d:
            dbp=str(Path(d)/'core.sqlite3')
            db=connect(dbp);enqueue(db,'shell',{'command':'echo should-not-run'},'x1');db.close()
            run(dbp,'qa-worker')
            db=connect(dbp);row=db.execute("SELECT status,result FROM tasks WHERE id='x1'").fetchone();db.close()
            self.assertEqual(row[0],'failed')
            self.assertIn('unsupported task kind',row[1])

if __name__=='__main__':unittest.main()
