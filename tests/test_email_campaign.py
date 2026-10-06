import unittest
from email_queue import Queue, Campaign
from email_campaign import ContactBook, Template, report

class CampaignPreparationTests(unittest.TestCase):
    def test_import_dedupe_provenance_segmentation(self):
        q=Queue(); b=ContactBook(q)
        a=b.import_csv("email,name,segments\nPASTOR@x.org,Joao,pastores|ms\nbad,,pastores\n","directory-a")
        c=b.import_csv("email,name,segments\npastor@x.org,,lideres\n","referral-b")
        self.assertEqual(a,{"rows":2,"accepted":1,"invalid":1,"duplicates":0})
        self.assertEqual(c["duplicates"],1)
        p=b.profiles["pastor@x.org"]
        self.assertEqual(p.provenance,["directory-a","referral-b"])
        self.assertEqual(set(p.segments),{"pastores","ms","lideres"})
        self.assertEqual(len(b.segment("pastores")),1)
        q.suppress("pastor@x.org","UNSUBSCRIBED")
        self.assertEqual(b.segment("pastores"),[])

    def test_template_requires_unsubscribe(self):
        p=ContactBook(Queue()); p.import_csv("email,name,segments\na@b.com,Ana,pastores\n","x")
        contact=p.profiles["a@b.com"]
        with self.assertRaises(ValueError): Template("Oi {{name}}","corpo").render(contact,"https://x/u/1")
        s,b=Template("Oi {{name}}","Mensagem\n{{unsubscribe_url}}").render(contact,"https://x/u/1")
        self.assertEqual(s,"Oi Ana"); self.assertIn("https://x/u/1",b)

    def test_reporting_is_campaign_scoped(self):
        q=Queue(); a=Campaign("a",True,True); b=Campaign("b",True,True)
        da=q.enqueue(a,"a@b.com","fake"); q.enqueue(b,"b@b.com","fake")
        q.record_result(da,"DELIVERED")
        self.assertEqual(report(q,"a"),{"DELIVERED":1})
        self.assertEqual(report(q,"b"),{"QUEUED":1})

if __name__=="__main__": unittest.main()
