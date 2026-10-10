import unittest

from tiktok_api import (
    CREATOR_INFO_PATH,
    DIRECT_POST_PATH,
    STATUS_PATH,
    TikTokApiError,
    classify_error,
    fetch_publish_status,
    init_direct_post_from_url,
    preflight,
)


class TikTokApiTests(unittest.TestCase):
    def test_preflight_verifies_exact_creator_without_returning_token(self):
        seen = {}
        def transport(path, payload, token):
            seen.update(path=path, payload=payload, token=token)
            return 200, {
                "data": {
                    "creator_username": "universo.anthares",
                    "privacy_level_options": ["SELF_ONLY"],
                    "max_video_post_duration_sec": 600,
                },
                "error": {"code": "ok", "message": "", "log_id": "log-1"},
            }
        result = preflight("secret-token", "@universo.anthares", transport=transport)
        self.assertEqual(seen["path"], CREATOR_INFO_PATH)
        self.assertEqual(seen["token"], "secret-token")
        self.assertTrue(result["identity_verified"])
        self.assertFalse(result["token_exported"])
        self.assertNotIn("secret-token", repr(result))

    def test_unaudited_restriction_is_a_first_class_blocker(self):
        def transport(path, payload, token):
            return 400, {
                "data": {},
                "error": {
                    "code": "unaudited_client_can_only_post_to_private_accounts",
                    "message": "restricted",
                    "log_id": "log-2",
                },
            }
        with self.assertRaises(TikTokApiError) as ctx:
            init_direct_post_from_url(
                "secret-token",
                video_url="https://media.example.test/video.mp4",
                title="Anthares",
                privacy_level="PUBLIC_TO_EVERYONE",
                transport=transport,
            )
        self.assertEqual(
            classify_error(ctx.exception.code),
            "app_audit_required_for_public_posting",
        )
        self.assertNotIn("secret-token", str(ctx.exception))

    def test_direct_post_uses_official_pull_from_url_shape(self):
        seen = {}
        def transport(path, payload, token):
            seen.update(path=path, payload=payload)
            return 200, {
                "data": {"publish_id": "v_pub_url~v2.123"},
                "error": {"code": "ok", "message": "", "log_id": "log-3"},
            }
        publish_id = init_direct_post_from_url(
            "token",
            video_url="https://media.example.test/video.mp4",
            title="Anthares",
            privacy_level="SELF_ONLY",
            transport=transport,
        )
        self.assertEqual(publish_id, "v_pub_url~v2.123")
        self.assertEqual(seen["path"], DIRECT_POST_PATH)
        self.assertEqual(seen["payload"]["source_info"]["source"], "PULL_FROM_URL")

    def test_status_preserves_documented_public_post_ids(self):
        def transport(path, payload, token):
            self.assertEqual(path, STATUS_PATH)
            return 200, {
                "data": {
                    "status": "PUBLISH_COMPLETE",
                    "publicaly_available_post_id": [123456],
                    "uploaded_bytes": 10,
                },
                "error": {"code": "ok", "message": "", "log_id": "log-4"},
            }
        result = fetch_publish_status("token", "publish-1", transport=transport)
        self.assertEqual(result["status"], "PUBLISH_COMPLETE")
        self.assertEqual(result["publicaly_available_post_id"], [123456])

    def test_video_url_must_be_https(self):
        with self.assertRaisesRegex(ValueError, "https_video_url_required"):
            init_direct_post_from_url(
                "token",
                video_url="http://example.test/video.mp4",
                title="x",
                privacy_level="SELF_ONLY",
            )


if __name__ == "__main__":
    unittest.main()
