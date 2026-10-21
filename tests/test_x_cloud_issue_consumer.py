import unittest
from unittest.mock import patch

from tools import x_cloud_issue_consumer as consumer


class XCloudConsumerTests(unittest.TestCase):
    def payload(self, **kw):
        p = {
            "platform": "x", "account": "lucasyahn", "duration_class": "long",
            "source_id": "stream-1", "segment_start": 600, "segment_end": 1240,
            "caption": "Um conteúdo de teste controlado.",
            "media_url": "https://raw.githubusercontent.com/UniversoAnthares/repo/x-media/video.mp4",
        }
        p.update(kw)
        return p

    def test_unique_idempotency_per_source_segment(self):
        first = consumer._idempotency(self.payload())
        self.assertEqual(first, consumer._idempotency(self.payload()))
        second = consumer._idempotency(self.payload(segment_start=1380))
        self.assertNotEqual(first, second)
        self.assertGreaterEqual(len(first), 12)

    def test_old_started_item_never_reposts(self):
        issue = {"number": 123}
        with patch.object(consumer, "_payload", return_value=self.payload()), \
             patch.object(consumer, "_comments", return_value=[
                 {"body": "X_POST_SUBMISSION_STARTED_V1"}]), \
             patch.object(consumer, "_worker", return_value={"status": "UNKNOWN_UNCERTAIN"}) as worker:
            result = consumer._process(issue)
        self.assertEqual(result, "UNCERTAIN_PREEXISTING_RECONCILE")
        self.assertEqual(worker.call_count, 1)
        self.assertIn("/post-status", worker.call_args.args[0])

    def test_readback_confirms_without_reposting(self):
        issue = {"number": 123}
        url = "https://x.com/lucasyahn/status/2109698725161631921"
        with patch.object(consumer, "_payload", return_value=self.payload()), \
             patch.object(consumer, "_comments", return_value=[
                 {"body": "X_POST_SUBMISSION_STARTED_V1"}]), \
             patch.object(consumer, "_worker", return_value={
                 "status": "CONFIRMED", "post_url": url}) as worker, \
             patch.object(consumer, "_github", return_value={}) as github:
            self.assertEqual(consumer._process(issue), "RECOVERED_CONFIRMED " + url)
        self.assertEqual(worker.call_count, 1)
        self.assertEqual(github.call_count, 2)

    def test_preexisting_uncertain_does_not_block_next(self):
        with patch.dict("os.environ", {
                "GITHUB_ACTIONS": "true", "RUNNER_ENVIRONMENT": "github-hosted",
                "RUNNER_OS": "Linux", "GH_TOKEN": "fake", "X_WORKER_CLIENT_TOKEN": "fake"}), \
             patch.object(consumer, "_list_open_x", return_value=[
                 {"number": 1}, {"number": 2}]), \
             patch.object(consumer, "_process", side_effect=[
                 "UNCERTAIN_PREEXISTING_RECONCILE", "CONFIRMED https://x.com/lucasyahn/status/2109698725161631921"]) as process:
            self.assertEqual(consumer.main(), 0)
            self.assertEqual(process.call_count, 2)

    def test_new_uncertain_ends_run(self):
        with patch.dict("os.environ", {
                "GITHUB_ACTIONS": "true", "RUNNER_ENVIRONMENT": "github-hosted",
                "RUNNER_OS": "Linux", "GH_TOKEN": "fake", "X_WORKER_CLIENT_TOKEN": "fake"}), \
             patch.object(consumer, "_list_open_x", return_value=[
                 {"number": 1}, {"number": 2}]), \
             patch.object(consumer, "_process", return_value="UNCERTAIN_NEW_SUBMISSION") as process:
            self.assertEqual(consumer.main(), 3)
            self.assertEqual(process.call_count, 1)

    def test_daily_quota_prevents_irreversible_post(self):
        issue = {"number": 126}
        with patch.object(consumer, "_payload", return_value=self.payload()), \
             patch.object(consumer, "_comments", return_value=[]), \
             patch.object(consumer, "_confirmed_today", return_value=10), \
             patch.object(consumer, "_worker") as worker, \
             patch.object(consumer, "_github") as github:
            self.assertEqual(consumer._process(issue), "X_DAILY_QUOTA_CONFIRMED")
            worker.assert_not_called()
            github.assert_not_called()

    def test_block_local_execution(self):
        with patch.dict("os.environ", {"GITHUB_ACTIONS": "false",
                                       "GH_TOKEN": "fake", "X_WORKER_CLIENT_TOKEN": "fake"}):
            with self.assertRaisesRegex(RuntimeError, "CLOUD_ONLY"):
                consumer.main()


if __name__ == "__main__":
    unittest.main()
