"""Offline tests of Resend suppression reconciliation; no API writes."""
import os
import tempfile
import unittest
from resend_suppression_sync import fetch_suppressions, sync
from pastor_mailing_queue import PastoralQueue

A = "e169aa45-1ecf-4183-9955-b1499d5701d3"
B = "e169aa45-1ecf-4183-9955-b1499d5701d4"
class SuppressionSyncTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.q=PastoralQueue(os.path.join(self.folder.name,"db.sqlite3"))
        self.q.import_directory([("Ana Souza","ana@example.org"),
                                 ("José Filho","jose@example.org")],"directory")

    def tearDown(self):
        self.folder.cleanup()

    def test_complete_pages_before_writes(self):
        routes=[]
        def transport(route):
            routes.append(route)
            if "after=" not in route:
                return {"data":[{"id":A,"email":"Ana@Example.org","origin":"bounce"}],
                        "has_more":True}
            return {"data":[{"id":B,"email":"jose@example.org","origin":"complaint"}],
                    "has_more":False}
        data=fetch_suppressions("not_used",transport)
        self.assertEqual(len(data),2)
        self.assertIn("after=",routes[1])
        report=sync(self.q,data)
        self.assertEqual(report["newly_suppressed"],2)
        self.assertEqual(self.q.status()["suppressed"],2)
        self.assertEqual(sync(self.q,data)["newly_suppressed"],0)

    def test_fail_closed_if_missing_more_flag(self):
        with self.assertRaises(RuntimeError):
            fetch_suppressions("mock",lambda p: {"data":[]})
        self.assertEqual(self.q.status()["suppressed"],0)

    def test_invalid_origin_blocks_read(self):
        with self.assertRaises(RuntimeError):
            fetch_suppressions("mock",lambda p: {"data":[
                {"id":A,"email":"ana@example.org","origin":"soft_bounce"}],
                "has_more":False})
        self.assertEqual(self.q.status()["suppressed"],0)

    def test_unrelated_suppression_not_imported(self):
        result=sync(self.q,[{"id":A,"email":"unknown@example.org","origin":"manual"}])
        self.assertEqual(result["outside_local_queue"],1)
        self.assertEqual(self.q.status()["suppressed"],0)

if __name__=="__main__":
    unittest.main()
