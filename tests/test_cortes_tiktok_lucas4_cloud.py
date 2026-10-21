import base64,importlib.util,json,os,sys,unittest,zlib
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"direct-tiktok-publisher"))
spec=importlib.util.spec_from_file_location("lucas4",ROOT/"tools"/"cortes_tiktok_lucasrosalem4_cloud_publish.py")
q=importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)

class SecondaryCloudTests(unittest.TestCase):
    def test_isolates_identity_and_account(self):
        self.assertEqual(q.ACCOUNT,"lucasrosalem4")
        self.assertIn("cortestiktok4",q.QUEUE)
        self.assertEqual(q.AUDIENCE,"https://anthares-remote-primary.vercel.app/api/cortes-tiktok")
        self.assertTrue(q.SEGMENT.fullmatch("g1:fOmihuHUT1M:4512:4561"))
        self.assertFalse(q.SEGMENT.fullmatch("../unsafe"))
        self.assertTrue(q.VID.fullmatch("7699234172166081810"))

    def test_marker_is_deterministic_and_per_account(self):
        sid="g1:9CIk-I_3VhM:7216:7273"
        got=q.marker(sid)
        self.assertRegex(got,r"^#anthares[a-f0-9]{10}$")
        self.assertNotEqual(got,q.marker("g1:9CIk-I_3VhM:7273:7320"))

    def test_session_secret_is_compressed_and_never_raw(self):
        state={"cookies":[{"name":"sessionid","domain":".tiktok.com",
                           "value":"test-never-real","expires":-1}],"origins":[]}
        raw=base64.b64encode(zlib.compress(json.dumps(state).encode(),9)).decode()
        with patch.dict(os.environ,{"TIKTOK_LUCASROSALEM4_STORAGE_STATE":raw}):
            self.assertEqual(q.state_from_secret()["cookies"][0]["name"],"sessionid")
        with patch.dict(os.environ,{"TIKTOK_LUCASROSALEM4_STORAGE_STATE":json.dumps(state)}):
            with self.assertRaises(q.SafeStop):
                q.state_from_secret()

    def test_guard_unauthorized_without_oidc(self):
        with patch.dict(os.environ,{"ACTIONS_ID_TOKEN_REQUEST_URL":"",
                                    "ACTIONS_ID_TOKEN_REQUEST_TOKEN":""},clear=True):
            with self.assertRaises(q.SafeStop):
                q.oidc()

    def test_cloud_starts_are_budgeted_by_second_account(self):
        source=(ROOT/"infra"/"neon-cortes-lucasrosalem4"/"index.mjs").read_text(encoding="utf-8")
        self.assertIn("const TARGET='tiktok:lucasrosalem4'",source)
        self.assertIn("cortes_tiktok_lucasrosalem4_publications",source)
        self.assertIn("action==='mirror'",source)
        self.assertIn("cortes_tiktok_publications",source)
        self.assertNotIn("if(claims.repository===CLIPPER){role='producer'",source)

if __name__=="__main__":
    unittest.main()
