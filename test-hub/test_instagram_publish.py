#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "instagram_publish.py"
spec = importlib.util.spec_from_file_location("instagram_publish", MODULE_PATH)
assert spec and spec.loader
instagram_publish = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = instagram_publish
spec.loader.exec_module(instagram_publish)

InstagramClient = instagram_publish.InstagramClient
InstagramAPIError = instagram_publish.InstagramAPIError


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class InstagramPublisherTests(unittest.TestCase):
    def setUp(self):
        self.client = InstagramClient("17890000000000000", "secret-token")

    def test_quota_reads_runtime_total(self):
        with patch.object(
            self.client,
            "_request",
            return_value={
                "data": [
                    {
                        "quota_usage": 7,
                        "config": {"quota_total": 50, "quota_duration": 86400},
                    }
                ]
            },
        ):
            quota = self.client.get_quota()
        self.assertEqual(quota.usage, 7)
        self.assertEqual(quota.total, 50)
        self.assertEqual(quota.remaining, 43)
        self.assertEqual(quota.duration, 86400)

    def test_create_reel_uses_official_container_fields(self):
        with patch.object(self.client, "_request", return_value={"id": "container-1"}) as request:
            container_id = self.client.create_reel_container(
                "https://cdn.example.test/video.mp4", "caption", True
            )
        self.assertEqual(container_id, "container-1")
        _, path = request.call_args.args
        self.assertEqual(path, "17890000000000000/media")
        data = request.call_args.kwargs["data"]
        self.assertEqual(data["media_type"], "REELS")
        self.assertEqual(data["video_url"], "https://cdn.example.test/video.mp4")
        self.assertTrue(data["share_to_feed"])

    def test_wait_until_ready_handles_processing(self):
        with patch.object(
            self.client,
            "container_status",
            side_effect=[
                {"status_code": "IN_PROGRESS"},
                {"status_code": "FINISHED", "status": "ready"},
            ],
        ), patch.object(instagram_publish.time, "sleep"):
            result = self.client.wait_until_ready("container-1", interval=0, attempts=2)
        self.assertEqual(result["status_code"], "FINISHED")

    def test_publish_reel_stops_when_quota_is_exhausted(self):
        quota = instagram_publish.Quota(50, 50, 86400, {})
        with patch.object(self.client, "get_quota", return_value=quota), patch.object(
            self.client, "create_reel_container"
        ) as create:
            with self.assertRaises(InstagramAPIError):
                self.client.publish_reel("https://cdn.example.test/video.mp4")
        create.assert_not_called()

    def test_publish_reel_runs_container_status_and_publish(self):
        quota = instagram_publish.Quota(2, 50, 86400, {})
        with patch.object(self.client, "get_quota", return_value=quota), patch.object(
            self.client, "create_reel_container", return_value="container-1"
        ), patch.object(
            self.client,
            "wait_until_ready",
            return_value={"status_code": "FINISHED"},
        ), patch.object(self.client, "publish_container", return_value="media-1"):
            result = self.client.publish_reel("https://cdn.example.test/video.mp4")
        self.assertEqual(result["media_id"], "media-1")
        self.assertEqual(result["quota_before_publish"]["remaining"], 48)

    @patch("urllib.request.urlopen")
    def test_access_token_is_sent_in_header(self, urlopen):
        urlopen.return_value = FakeResponse({"data": []})
        self.client.get_quota()
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer secret-token")
        self.assertNotIn("secret-token", request.full_url)


if __name__ == "__main__":
    unittest.main()
