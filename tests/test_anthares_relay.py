import os
import tempfile
import unittest
from anthares_relay.engine import Relay
from anthares_relay.adapters import IdentityProof, PublicationProof, AuthenticatedAdapter

class RelayTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.r=Relay(os.path.join(self.temp.name,"relay.db"))
 def tearDown(self):
  self.r.db.close()
  self.temp.cleanup()
 def test_duplicate_never_requeues(self):
  a=self.r.enqueue("lucasrosalem",b"video")
  self.assertEqual(a,self.r.enqueue("lucasrosalem",b"video"))
  self.assertEqual(a["state"],"queued")
 def test_identity_and_fencing(self):
  job=self.r.enqueue("lucasrosalem",b"video")["id"]
  with self.assertRaises(PermissionError): self.r.lease(job,False)
  token=self.r.lease(job,True)
  with self.assertRaises(ValueError): self.r.lease(job,True)
  with self.assertRaises(PermissionError): self.r.submitted(job,"wrong")
  self.r.submitted(job,token)
  with self.assertRaises(ValueError): self.r.verify(job,"id","https://kwai.com/v/1",lambda *_:False)
  self.assertEqual(self.r.status(),{"uncertain":1})
  self.r.verify(job,"id","https://kwai.com/v/1",lambda *_:True)
  self.assertEqual(self.r.status(),{"published":1})
  with self.assertRaises(ValueError): self.r.lease(job,True)
 def test_expired_lease_never_auto_retries(self):
  job=self.r.enqueue("lucasrosalem",b"other")["id"]
  self.r.lease(job,True)
  self.r.db.execute("UPDATE jobs SET expires=0 WHERE id=?",(job,))
  self.assertEqual(self.r.quarantine_expired(),1)
  self.assertEqual(self.r.status(),{"uncertain":1})

class AdapterTests(unittest.TestCase):
 def test_identity_rejects_truthy_string(self):
  self.assertFalse(IdentityProof("kwai","lucasrosalem","yes",True).valid_for("kwai","lucasrosalem"))
  self.assertFalse(IdentityProof("kwai","other",True,True).valid_for("kwai","lucasrosalem"))
 def test_publication_rejects_untrusted_host(self):
  self.assertFalse(PublicationProof("id","https://kwai.com.evil.example/video",True).valid())
  self.assertFalse(PublicationProof("id","https://www.kwai.com/video","yes").valid())
 def test_adapter_refuses_unimplemented_post(self):
  with self.assertRaises(PermissionError):
   AuthenticatedAdapter().publish(b"video",IdentityProof("kwai","other",True,True))
  with self.assertRaises(NotImplementedError):
   AuthenticatedAdapter().publish(b"video",IdentityProof("kwai","lucasrosalem",True,True))

if __name__=="__main__": unittest.main()
