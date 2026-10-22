import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from tools import cortes_pinterest_metadata_qa as qa

class QAStopsDespiteFailures(unittest.TestCase):
 def test_bounded_attempts_persist_cursor(self):
  jobs=[{'id':f'cortes-fanout-pinterest-{i:032x}','media_url':'http://invalid.example/no.mp4'} for i in range(1,5)]
  with tempfile.TemporaryDirectory() as tmp:
   with patch.object(qa,'CACHE',Path(tmp)/'.pinterest-transcripts'), \
        patch.object(qa,'call',return_value={'ok':True,'jobs':jobs}) as remote, \
        patch.object(qa,'qa_incident'):
    self.assertEqual(qa.metadata_qa(3),0)
    self.assertEqual(remote.call_count,1)
    self.assertEqual((Path(tmp)/'.pinterest-qa-title-cursor').read_text(encoding='utf8'),jobs[2]['id'])

if __name__=='__main__':unittest.main()
