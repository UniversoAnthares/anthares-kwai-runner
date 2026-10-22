"""QA must handle both Neon JSONB wire encodings, without stopping after one video."""
import unittest
from unittest.mock import patch
from tools import cortes_pinterest_metadata_qa as qa
class JsonbEvidenceQA(unittest.TestCase):
 def test_string_evidence_does_not_stop_next_404(self):
  jobs=[{'id':'job1','media_url':'https://anthares.us/wp-content/uploads/anthares-clips/a.mp4'},
        {'id':'job2','media_url':'https://anthares.us/wp-content/uploads/anthares-clips/b.mp4'}]
  def mocked(action,body):
   if action=='qa-media-pending':return {'ok':True,'jobs':jobs}
   return {'ok':True,'job':{'status':'queued','confirmation_evidence':'{"kind":"source_media_invalid"}'}}
  with patch.object(qa,'call',side_effect=mocked),patch.object(qa,'media_status',return_value=404):
   self.assertEqual(qa.media_qa(),2)
if __name__=='__main__':unittest.main()
