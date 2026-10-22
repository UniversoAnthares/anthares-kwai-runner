import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from tools import cortes_buffer_pinterest_cloud as p


class ReconcileWhenQuotaClosed(unittest.TestCase):
    def test_reconcile_precedes_closed_budget_and_does_not_publish(self):
        actions = []
        def queue(name, payload=None):
            actions.append(name)
            if name == "cooldown-status":
                return {"active": False}
            if name == "pending":
                return {"jobs": []}
            if name == "policy":
                return {"enabled": False, "remaining": 0, "used": 20}
            raise AssertionError("Unexpected queue action: " + name)
        with patch.object(p, "cloud_only"), patch.object(p, "queue", side_effect=queue), \
             patch.object(p, "reconcile", return_value=2) as reconcile, \
             patch.object(p, "board_gate") as board, \
             patch.object(p, "publish_once") as publish:
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(p.main(), 0)
        reconcile.assert_called_once()
        board.assert_not_called()
        publish.assert_not_called()
        self.assertEqual(actions, ["cooldown-status", "pending", "policy"])
        record = json.loads(out.getvalue().splitlines()[-1])
        self.assertEqual(record["posts_confirmed_this_run"], 2)
        self.assertEqual(record["pinterest_cloud"], "PASS")


    def test_backpressure_prevents_new_buffer_mutation(self):
        actions=[]
        def queue(name,payload=None):
            actions.append(name)
            if name=="cooldown-status":return {"active":False}
            if name=="pending":return {"jobs":[{"id":str(i)} for i in range(8)]}
            raise AssertionError("Unexpected queue action: "+name)
        with patch.object(p,"cloud_only"),patch.object(p,"queue",side_effect=queue),\
             patch.object(p,"reconcile",return_value=0),\
             patch.object(p,"board_gate") as board,patch.object(p,"publish_once") as publish:
            output=io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(p.main(),0)
        board.assert_not_called()
        publish.assert_not_called()
        self.assertEqual(actions,["cooldown-status","pending"])
        state=json.loads(output.getvalue().splitlines()[-1])
        self.assertEqual(state["pinterest_cloud"],"BACKPRESSURE_BUFFER")
        self.assertEqual(state["buffer_pending_count"],8)

if __name__ == "__main__":
    unittest.main()
