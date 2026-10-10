import json
import tempfile
import unittest
from pathlib import Path
from anthares_core.queue import connect,enqueue,claim,finish
from anthares_core.state_store import export_state,import_state

class StateStoreTests(unittest.TestCase):
    def test_round_trip_preserves_queue(self):
        with tempfile.TemporaryDirectory() as d:
            a=str(Path(d)/'a.sqlite3');b=str(Path(d)/'b.sqlite3');state=str(Path(d)/'state.json')
            db=connect(a)
            enqueue(db,'probe',{'x':1},'one')
            task=claim(db,'w1',120)
            self.assertTrue(finish(db,task['id'],task['token'],{'ok':True}))
            enqueue(db,'probe',{'x':2},'two')
            db.close()
            self.assertEqual(export_state(a,state),2)
            doc=json.loads(Path(state).read_text())
            self.assertEqual(doc['schema'],'anthares.core.state.v1')
            self.assertEqual(import_state(state,b),2)
            db2=connect(b)
            rows=db2.execute('SELECT id,status,result FROM tasks ORDER BY id').fetchall()
            db2.close()
            self.assertEqual(rows[0][0:2],('one','done'))
            self.assertEqual(json.loads(rows[0][2]),{'ok':True})
            self.assertEqual(rows[1][0:2],('two','queued'))

if __name__=='__main__':unittest.main()
