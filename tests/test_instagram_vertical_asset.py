"""Instagram aspect and derivative contracts; never touch network or WordPress in unit tests."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from tools import cortes_instagram_vertical_asset as asset


class VerticalInstagramAssetTests(unittest.TestCase):
    def test_exact_ratio_requires_real_9_16(self):
        self.assertTrue(asset.exact_vertical(720, 1280))
        self.assertTrue(asset.exact_vertical(1080, 1920))
        self.assertFalse(asset.exact_vertical(1920, 1080))
        self.assertFalse(asset.exact_vertical(719, 1280))
        self.assertFalse(asset.exact_vertical(0, 1280))

    def test_original_vertical_reuses_master_without_upload(self):
        source = "https://anthares.us/wp-content/uploads/anthares-clips/2026/11/clip.mp4"
        with patch.object(asset, "_known_dimensions", return_value=(1080, 1920)), \
             patch.object(asset, "_upload") as upload, \
             patch.object(asset, "_download") as download:
            self.assertEqual(asset.ensure_vertical_media(source, "job1", 42), source)
            upload.assert_not_called()
            download.assert_not_called()

    def test_landscape_existing_exact_derivative_is_reused(self):
        source = "https://anthares.us/wp-content/uploads/anthares-clips/2026/11/clip.mp4"
        derivative = "https://anthares.us/wp-content/uploads/2026/11/cortes-ig9x16-1234567890.mp4"
        with patch.object(asset, "_known_dimensions", return_value=(1920, 1080)), \
             patch.object(asset, "_existing", return_value=derivative), \
             patch.object(asset, "_probe", return_value=(720, 1280)), \
             patch.object(asset, "_download") as download:
            self.assertEqual(asset.ensure_vertical_media(source, "job2", 42), derivative)
            download.assert_not_called()

    def test_horizontal_rejects_unverified_existing_derivative(self):
        source = "https://anthares.us/wp-content/uploads/anthares-clips/2026/11/clip.mp4"
        with patch.object(asset, "_known_dimensions", return_value=(1920, 1080)), \
             patch.object(asset, "_existing", return_value="https://anthares.us/test.mp4"), \
             patch.object(asset, "_probe", return_value=(1920, 1080)):
            with self.assertRaisesRegex(RuntimeError, "EXISTING_RATIO_INVALID"):
                asset.ensure_vertical_media(source, "job3")

    def test_untrusted_media_host_and_credentials_are_rejected(self):
        for url in ("https://evil.example/a.mp4", "http://anthares.us/a.mp4",
                    "https://anthares.us/a.mp4?fake=1"):
            with self.assertRaisesRegex(RuntimeError, "SOURCE_INVALID"):
                asset._source_url(url)

    def test_storage_boundary_does_not_accept_missing_credential(self):
        with patch.dict(asset.os.environ, {"WP_SITE_URL": "https://anthares.us",
              "WP_USERNAME": "", "WP_APP_PASSWORD": ""}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "CREDENTIAL_MISSING"):
                asset._auth()


if __name__ == "__main__":
    unittest.main()
