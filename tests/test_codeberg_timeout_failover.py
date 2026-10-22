import importlib.util,pathlib,sys,unittest
from unittest.mock import patch,Mock
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"direct-tiktok-publisher"))
spec=importlib.util.spec_from_file_location("lucas4",ROOT/"tools"/"cortes_tiktok_lucasrosalem4_cloud_publish.py")
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
class CodebergTimeoutTests(unittest.TestCase):
 def test_prestart_claim_falls_back_on_timeout(self):
  response=Mock()
  response.__enter__=Mock(return_value=response)
  response.__exit__=Mock(return_value=False)
  with patch.object(p.urllib.request,"urlopen",side_effect=[TimeoutError(),response]) as caller:
   with patch.object(p,"read_json",return_value={"ok":True,"job":None}):
    self.assertTrue(p.call("claim","fake-token",{})["ok"])
    self.assertEqual(caller.call_count,2)
 def test_never_retry_irreversible_start(self):
  with patch.object(p.urllib.request,"urlopen",side_effect=TimeoutError()) as caller:
   with self.assertRaises(p.SafeStop):
    p.call("start","fake-token",{"id":"test"})
   self.assertEqual(caller.call_count,1)
if __name__=="__main__":unittest.main()
