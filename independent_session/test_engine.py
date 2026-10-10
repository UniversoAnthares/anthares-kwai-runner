import os,subprocess,sys,tempfile,unittest
from pathlib import Path
from engine import encrypt,decrypt
class VaultTests(unittest.TestCase):
    def test_roundtrip(self):
        original=b"synthetic session bytes"+os.urandom(64)
        sealed=encrypt(original,"synthetic test key only","lucasrosalem")
        self.assertEqual(decrypt(sealed,"synthetic test key only","lucasrosalem"),original)
    def test_wrong_identity(self):
        blob=encrypt(b"session","key","lucasrosalem")
        with self.assertRaises(ValueError):decrypt(blob,"key","other")
    def test_tamper(self):
        blob=bytearray(encrypt(b"session","key","lucasrosalem"))
        import json
        h=json.loads(blob);ct=bytearray.fromhex(h["ciphertext"]);ct[-1]^=1;h["ciphertext"]=ct.hex()
        with self.assertRaises(Exception):decrypt(json.dumps(h).encode(),"key","lucasrosalem")
    def test_wrong_key(self):
        blob=encrypt(b"session","key","lucasrosalem")
        with self.assertRaises(Exception):decrypt(blob,"wrong","lucasrosalem")
if __name__=="__main__":unittest.main()
