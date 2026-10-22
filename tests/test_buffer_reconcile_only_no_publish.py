"""Reconcile existing Buffer receipts without creating any new post."""
import os
import unittest
from unittest.mock import patch
from tools import cortes_buffer_instagram_cloud as ig
from tools import cortes_buffer_linkedin_cloud as li
from tools import cortes_buffer_pinterest_cloud as pin


class ReconcileNoNewPosts(unittest.TestCase):
    def _reconcile_only(self, module):
        with (patch.dict(os.environ, {"CORTES_RECONCILE_ONLY":"1"}),
              patch.object(module, "cloud_only"),
              patch.object(module, "queue",return_value={"active":False}) as queue,
              patch.object(module, "reconcile",return_value=2) as reconciler,
              patch.object(module, "publish_once") as publisher):
            self.assertEqual(module.main(),0)
            reconciler.assert_called_once()
            publisher.assert_not_called()
            actions=[call.args[0] for call in queue.call_args_list]
            self.assertNotIn("lease",actions)
            self.assertNotIn("start",actions)
            self.assertNotIn("scheduled",actions)
            self.assertNotIn("policy",actions)

    def test_instagram_reconcile_only(self):self._reconcile_only(ig)
    def test_linkedin_reconcile_only(self):self._reconcile_only(li)
    def test_pinterest_reconcile_only(self):self._reconcile_only(pin)

    def _exhausted_quota_still_reconciles(self,module):
        def read(action,*args):
            if action=="cooldown-status":return {"active":False}
            if action=="policy":return {"enabled":False,"remaining":0,"used":20}
            raise AssertionError("Unexpected queue mutation "+str(action))
        with (patch.dict(os.environ, {"CORTES_RECONCILE_ONLY":"0"}),
              patch.object(module,"cloud_only"),
              patch.object(module,"queue",side_effect=read),
              patch.object(module,"reconcile",return_value=1) as reconciler,
              patch.object(module,"publish_once") as publisher):
            self.assertEqual(module.main(),0)
            reconciler.assert_called_once()
            publisher.assert_not_called()

    def test_linkedin_exhausted_quota_readback(self):self._exhausted_quota_still_reconciles(li)
    def test_instagram_exhausted_quota_readback(self):self._exhausted_quota_still_reconciles(ig)


if __name__=="__main__":unittest.main()
