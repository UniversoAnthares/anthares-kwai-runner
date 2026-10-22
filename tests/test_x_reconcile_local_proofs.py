import unittest

from tools.x_reconcile_local_proofs import reconcile
from tools.x_issue_publisher import fingerprint

BODY = {
    "platform": "x",
    "account": "lucasyahn",
    "duration_class": "long",
    "source_id": "cortes-facebook-long-20261020",
    "scan_start": 0,
    "segment_start": 5640,
    "segment_end": 6240,
    "microedit": {"final_duration": 560},
}
URL = "https://x.com/lucasyahn/status/2113103163859313089"


class XReconcileLocalProofsTests(unittest.TestCase):
    def issue(self):
        import json
        return {
            "state": "closed",
            "title": "[X-PUBLISH] test",
            "body": "```json\n" + json.dumps(BODY) + "\n```",
        }

    def comments(self, *, author="UniversoAnthares", url=URL, video=True):
        import json
        return [{
            "user": {"login": author},
            "body": "X_LOCAL_VIDEO_CONFIRMED_V1\n" + json.dumps({
                "kind": "X_VIDEO_CONFIRMED_V1",
                "account": "lucasyahn",
                "video_verified": video,
                "post_url": url,
                "idempotency_key": fingerprint(BODY),
            })
        }]

    def test_matching_postgres_confirmed_video_is_trusted(self):
        proof = reconcile(self.issue(), self.comments(),
                          lambda k: {"ok": True, "status": "CONFIRMED", "post_url": URL})
        self.assertIsNotNone(proof)
        self.assertEqual(proof["post_url"], URL)
        self.assertTrue(proof["video_verified"])

    def test_no_trust_for_unconfirmed_or_different_post(self):
        for ledger in (
            {"ok": True, "status": "UNCERTAIN", "post_url": None},
            {"ok": True, "status": "CONFIRMED", "post_url": "https://x.com/lucasyahn/status/999"},
            {"ok": False, "status": "CONFIRMED", "post_url": URL},
        ):
            with self.subTest(ledger=ledger):
                self.assertIsNone(reconcile(self.issue(), self.comments(), lambda k: ledger))

    def test_missing_video_wrong_author_and_wrong_account_rejected(self):
        self.assertIsNone(reconcile(self.issue(), self.comments(video=False),
                                    lambda k: {"ok": True, "status": "CONFIRMED", "post_url": URL}))
        self.assertIsNone(reconcile(self.issue(), self.comments(author="otheruser"),
                                    lambda k: {"ok": True, "status": "CONFIRMED", "post_url": URL}))
        wrong = self.issue()
        import json
        wrong["body"] = "```json\n" + json.dumps({**BODY, "account": "other"}) + "\n```"
        self.assertIsNone(reconcile(wrong, self.comments(),
                                    lambda k: {"ok": True, "status": "CONFIRMED", "post_url": URL}))

    def test_already_trusted_bot_comment_not_repeated(self):
        comments = self.comments()
        comments.append({"user": {"login": "github-actions[bot]"}, "body": "X_VIDEO_CONFIRMED_V1"})
        self.assertIsNone(reconcile(self.issue(), comments,
                                    lambda k: {"ok": True, "status": "CONFIRMED", "post_url": URL}))


if __name__ == "__main__":
    unittest.main()
