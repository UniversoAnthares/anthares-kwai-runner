import unittest
from email_queue import Queue, Campaign

class QueueTests(unittest.TestCase):
    def setUp(self):
        self.q=Queue()
        self.c=Campaign("pastors-draft", approved=True, recipient_set_approved=True, daily_cap=2)

    def test_dedupe_and_provenance(self):
        a=self.q.upsert_contact(" Pastor@Example.org ","source-a")
        b=self.q.upsert_contact("pastor@example.org","source-b")
        self.assertIs(a,b); self.assertEqual(a.sources,["source-a","source-b"])
        d1=self.q.enqueue(self.c,a.email,"brevo")
        d2=self.q.enqueue(self.c,a.email,"brevo")
        self.assertIs(d1,d2)

    def test_double_approval_gate(self):
        for c in [Campaign("x"), Campaign("x",approved=True), Campaign("x",recipient_set_approved=True)]:
            with self.assertRaises(PermissionError): self.q.enqueue(c,"a@b.com","fake")

    def test_suppression_rechecked_at_lease(self):
        d=self.q.enqueue(self.c,"a@b.com","brevo")
        self.q.suppress("A@B.COM","UNSUBSCRIBED")
        self.assertEqual(self.q.lease_batch(self.c,"brevo"),[])
        self.assertEqual(d.status,"SUPPRESSED")

    def test_provider_isolation(self):
        self.q.enqueue(self.c,"a@b.com","brevo")
        self.q.enqueue(self.c,"a@b.com","resend")
        self.assertEqual(len(self.q.lease_batch(self.c,"brevo")),1)
        self.assertEqual(len(self.q.lease_batch(self.c,"resend")),1)

    def test_gradual_cap(self):
        for i in range(4): self.q.enqueue(self.c,f"p{i}@example.org","brevo")
        self.assertEqual(len(self.q.lease_batch(self.c,"brevo")),2)

    def test_hard_bounce_suppresses_future_campaign(self):
        d=self.q.enqueue(self.c,"a@b.com","brevo")
        self.q.record_result(d,"BOUNCED_HARD")
        c2=Campaign("next",approved=True,recipient_set_approved=True)
        with self.assertRaises(PermissionError): self.q.enqueue(c2,"a@b.com","resend")

if __name__=="__main__": unittest.main()
