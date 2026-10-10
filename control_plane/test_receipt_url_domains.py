import unittest
from datetime import datetime, timezone
from persistent_publisher import PublishReceipt

class ReceiptDomainTests(unittest.TestCase):
    def receipt(self, url):
        return PublishReceipt.from_mapping(dict(platform="tiktok", provider="test", profile_id="p", account_handle="@universo.anthares", post_id="123", post_url=url, published_at=datetime.now(timezone.utc).isoformat(), content_sha256="a"*64, identity_verified=True, publication_verified=True))

    def test_valid_platform(self):
        self.assertEqual(self.receipt("https://www.tiktok.com/@universo.anthares/video/123").platform, "tiktok")

    def test_reject_external_domain(self):
        with self.assertRaisesRegex(RuntimeError, "receipt_post_url_platform_mismatch"):
            self.receipt("https://attacker.example/video/123")

    def test_reject_domain_suffix_trick(self):
        with self.assertRaisesRegex(RuntimeError, "receipt_post_url_platform_mismatch"):
            self.receipt("https://tiktok.com.attacker.example/video/123")

if __name__ == "__main__":
    unittest.main()
