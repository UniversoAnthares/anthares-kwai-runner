import base64
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools import kwai_session_vault_client as vault

class VaultClientTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=str(Path(self.tmp.name)/"kwai-session.enc")
        self.raw=b"Salted__"+b"x"*64
        self.ciphertext=base64.b64encode(self.raw).decode("ascii")
        self.doc={"schema":"anthares.kwai.vault.v1","account":"lucasrosalem",
                  "ciphertext":self.ciphertext,
                  "sha256":hashlib.sha256(self.ciphertext.encode()).hexdigest()}
    def tearDown(self):self.tmp.cleanup()
    def test_pull_encrypted_session_atomically(self):
        with patch.object(vault,"get_json",return_value=self.doc):
            self.assertEqual(vault.pull({"Authorization":"Bearer fake"},self.path),0)
        self.assertEqual(Path(self.path).read_bytes(),self.raw)
    def test_reject_tampered_session(self):
        d={**self.doc,"sha256":"0"*64}
        with patch.object(vault,"get_json",return_value=d):
            with self.assertRaisesRegex(RuntimeError,"digest mismatch"):
                vault.pull({},self.path)
        self.assertFalse(Path(self.path).exists())
    def test_reject_plaintext_session_upload(self):
        Path(self.path).write_bytes(b"cookies and passwords")
        with self.assertRaisesRegex(RuntimeError,"unencrypted"):
            vault.push({},self.path)
    def test_upload_never_logs_ciphertext(self):
        Path(self.path).write_bytes(self.raw)
        with patch.object(vault,"get_json",return_value={"ok":True,"stored":True}) as req:
            self.assertEqual(vault.push({},self.path),0)
        payload=req.call_args.kwargs["data"].decode()
        self.assertIn(self.ciphertext,payload)
        self.assertNotIn("KWAI_PASSWORD",payload)
    def test_probe_only_reports_availability(self):
        with patch.object(vault,"get_json",return_value={"ok":True,"persistent":True,"available":False}):
            vault.probe({})

if __name__=="__main__":unittest.main()
