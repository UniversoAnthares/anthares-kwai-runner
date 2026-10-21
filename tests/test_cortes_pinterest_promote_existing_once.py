"""No network. One-shot Pinterest Buffer Pin promotion contracts."""
import unittest
from unittest.mock import patch
from tools import cortes_pinterest_promote_existing_once as m
from social_adapters.buffer_three_channels import PINTEREST_PUBLIC_BOARD_ID

def row(status="buffer", board=PINTEREST_PUBLIC_BOARD_ID, link=""):
    return {"id":m.PINNED_ID,"channelId":m.CHANNEL,
            "channelService":"pinterest","schedulingType":"automatic",
            "status":status,"externalLink":link,
            "metadata":{"board":{"serviceId":board}}}

class FirstPinProof(unittest.TestCase):
    def test_wrong_board_cannot_mutate(self):
        with patch.dict(m.os.environ,{"GITHUB_ACTIONS":"true","RUNNER_ENVIRONMENT":"github-hosted",
                  "RUNNER_OS":"Linux","BUFFER_API_KEY":"fixture"}), \
             patch.object(m,"read_post",return_value=row(board="wrong")), \
             patch.object(m,"api") as api:
            with self.assertRaisesRegex(RuntimeError,"BOARD_UNVERIFIED"):m.main()
            api.assert_not_called()

    def test_already_sent_returns_public_url_without_mutation(self):
        live=row("sent",link="https://www.pinterest.com/pin/123456789/")
        with patch.dict(m.os.environ,{"GITHUB_ACTIONS":"true","RUNNER_ENVIRONMENT":"github-hosted",
                  "RUNNER_OS":"Linux","BUFFER_API_KEY":"fixture"}), \
             patch.object(m,"read_post",return_value=live), \
             patch.object(m,"api") as api:
            self.assertEqual(m.main(),0)
            api.assert_not_called()

    def test_share_now_is_only_one_mutation(self):
        states=[row(),row("sent",link="https://www.pinterest.com/pin/123456789/")]
        def returned(query):
            self.assertIn("editPost",query)
            self.assertIn("mode: shareNow",query)
            return {"editPost":{"post":{"id":m.PINNED_ID,"channelId":m.CHANNEL}}}
        with patch.dict(m.os.environ,{"GITHUB_ACTIONS":"true","RUNNER_ENVIRONMENT":"github-hosted",
                  "RUNNER_OS":"Linux","BUFFER_API_KEY":"fixture"}), \
             patch.object(m,"read_post",side_effect=states), \
             patch.object(m,"api",side_effect=returned) as api:
            self.assertEqual(m.main(),0)
            api.assert_called_once()

if __name__=="__main__":unittest.main()
