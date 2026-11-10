"""Read-only Buffer pending audit never mutates Neon or Buffer."""
import contextlib
import io
import json
import unittest
from unittest.mock import patch

from tools import cortes_buffer_pinterest_cloud as m


class BufferPendingAudit(unittest.TestCase):
    def test_old_failed_and_new_scheduled_are_distinguished(self):
        old="6ad914067d80fe56e7308119"
        new="6af3496842d372a81f6b4afd"
        out=io.StringIO()
        def fake_api(query):
            self.assertIn("CortesPinterestPendingAudit",query)
            return {
                "p0":{"id":old,"channelId":m.PINTEREST_ID,
                      "status":"failed","externalLink":None,
                      "schedulingType":"automatic",
                      "dueAt":"2026-10-21T19:00:00Z"},
                "p1":{"id":new,"channelId":m.PINTEREST_ID,
                      "status":"scheduled","externalLink":None,
                      "schedulingType":"automatic",
                      "dueAt":"2026-11-10T21:39:00Z"}
            }
        def fake_queue(action,*args):
            self.assertEqual(action,"pending")
            return {"jobs":[{"remote_id":old},{"remote_id":new}]}
        with patch.object(m,"queue",side_effect=fake_queue), \
             patch.object(m,"api",side_effect=fake_api), \
             contextlib.redirect_stdout(out):
            self.assertEqual(m.audit_stale_buffer_pending(),0)
        raw=out.getvalue()
        rows=[json.loads(line.split("=",1)[1]) for line in raw.splitlines()
              if line.startswith("PINTEREST_PENDING_AUDIT=")]
        self.assertEqual([x["status"] for x in rows],["failed","scheduled"])
        self.assertTrue(all(x["identity_verified"] for x in rows))
        self.assertNotIn(old,raw)
        self.assertNotIn(new,raw)
        self.assertIn('"cas_mutations":0',raw)

    def test_wrong_identity_never_claims_public_link(self):
        remote="6ad914067d80fe56e7308119"
        with patch.object(m,"queue",return_value={"jobs":[{"remote_id":remote}]}), \
             patch.object(m,"api",return_value={"p0":{
                 "id":remote,"channelId":"other-account","status":"sent",
                 "externalLink":"https://www.pinterest.com/pin/819514463494612668",
                 "schedulingType":"automatic","dueAt":None}}), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            m.audit_stale_buffer_pending()
        self.assertIn('"status":"IDENTITY_MISMATCH"',out.getvalue())
        self.assertIn('"public_link_verified":false',out.getvalue())


if __name__=="__main__":
    unittest.main()
