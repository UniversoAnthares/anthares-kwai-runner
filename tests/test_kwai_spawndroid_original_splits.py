"""Offline-only tests for the original signed split APK installation alternative."""
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SCRIPT = ROOT / "tools" / "kwai_spawndroid_original_splits.py"
spec = importlib.util.spec_from_file_location("kwai_original_splits", SCRIPT)
splits = importlib.util.module_from_spec(spec)
spec.loader.exec_module(splits)

SOURCE = {"original.example.test"}


def example(package="com.kwai.video"):
    count = splits.EXPECTED_COUNTS[package]
    names = ["base.apk"] + [f"split_{n}.apk" for n in range(1, count)]
    return {
        "package": package,
        "versionCode": 647103 if package == "com.kwai.video" else 647120,
        "files": [
            {"name": name, "bytes": 1024, "sha256": "a" * 64,
             "url": "https://original.example.test/private/" + name}
            for name in names
        ],
    }


class SplitManifestTests(unittest.TestCase):
    def test_regular_complete(self):
        doc = splits.validate_manifest(example(), SOURCE)
        self.assertEqual(len(doc["files"]), 25)
        self.assertEqual(doc["files"][0]["name"], "base.apk")
        print("KWAI_SPLITS_REGULAR_MANIFEST=PASS")

    def test_lite_complete(self):
        doc = splits.validate_manifest(example("kwai.lite.video"), SOURCE)
        self.assertEqual(len(doc["files"]), 18)
        print("KWAI_SPLITS_LITE_MANIFEST=PASS")

    def test_count_must_match_source_device(self):
        x = example()
        x["files"].pop()
        with self.assertRaisesRegex(splits.SplitError, "split_count_incomplete"):
            splits.validate_manifest(x, SOURCE)

    def test_base_required(self):
        x = example()
        x["files"][0]["name"] = "split_0.apk"
        x["files"][0]["url"] = "https://original.example.test/private/split_0.apk"
        with self.assertRaisesRegex(splits.SplitError, "base_missing"):
            splits.validate_manifest(x, SOURCE)

    def test_wrong_package_denied(self):
        x = example()
        x["package"] = "com.kwai.kuaishou.video.live"
        with self.assertRaisesRegex(splits.SplitError, "package_not_allowed"):
            splits.validate_manifest(x, SOURCE)

    def test_url_requires_https(self):
        x = example()
        x["files"][0]["url"] = "http://original.example.test/private/base.apk"
        with self.assertRaisesRegex(splits.SplitError, "host_denied"):
            splits.validate_manifest(x, SOURCE)

    def test_url_requires_approved_host(self):
        x = example()
        x["files"][0]["url"] = "https://evil.invalid/base.apk"
        with self.assertRaisesRegex(splits.SplitError, "host_denied"):
            splits.validate_manifest(x, SOURCE)

    def test_url_must_point_to_an_apk(self):
        x = example()
        x["files"][0]["url"] = "https://original.example.test/download.zip"
        with self.assertRaisesRegex(splits.SplitError, "not_direct_apk"):
            splits.validate_manifest(x, SOURCE)

    def test_duplicate_name_denied(self):
        x = example()
        x["files"][1]["name"] = "base.apk"
        with self.assertRaisesRegex(splits.SplitError, "duplicate_split_filename"):
            splits.validate_manifest(x, SOURCE)

    def test_duplicate_url_denied(self):
        x = example()
        x["files"][1]["url"] = x["files"][0]["url"]
        with self.assertRaisesRegex(splits.SplitError, "duplicate_split_url"):
            splits.validate_manifest(x, SOURCE)

    def test_no_hosts_is_blocked(self):
        with self.assertRaisesRegex(splits.SplitError, "allowed_asset_hosts_missing"):
            splits.validate_manifest(example(), set())

    def test_invalid_hash_denied(self):
        x = example()
        x["files"][0]["sha256"] = "b" * 63
        with self.assertRaisesRegex(splits.SplitError, "component_sha256_invalid"):
            splits.validate_manifest(x, SOURCE)

    def test_version_boolean_denied(self):
        x = example()
        x["versionCode"] = True
        with self.assertRaisesRegex(splits.SplitError, "version_invalid"):
            splits.validate_manifest(x, SOURCE)

    def test_bad_zip_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "base.apk"
            p.write_bytes(b"not_an_apk")
            with self.assertRaisesRegex(splits.SplitError, "split_zip_corrupt"):
                splits.verify_component(p, package="com.kwai.video", version=647103)

    def test_cryptographic_signer_check_is_enforced(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "base.apk"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("AndroidManifest.xml", b"mock")
            good = ("package: name='com.kwai.video' versionCode='647103' "
                    "versionName='13.10.10.647103'\n")
            signer = ("Verified using v2 scheme (APK Signature Scheme v2): true\n"
                      "Signer #1 certificate SHA-256 digest: " +
                      splits.guard.EXPECTED_CERT_SHA256 + "\n")
            with patch.object(splits.guard, "_tool", side_effect=lambda x, y: y), \
                 patch.object(splits.guard, "_run", side_effect=lambda argv: good if "badging" in argv else signer):
                self.assertEqual(splits.verify_component(p, package="com.kwai.video", version=647103),
                                 splits.guard.EXPECTED_CERT_SHA256)

    def test_wrong_signing_key_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "base.apk"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("AndroidManifest.xml", b"mock")
            bad = ("Verified using v2 scheme (APK Signature Scheme v2): true\n"
                   "Signer #1 certificate SHA-256 digest: " + ("1"*64) + "\n")
            good = ("package: name='com.kwai.video' versionCode='647103' "
                    "versionName='13.10.10.647103'\n")
            with patch.object(splits.guard, "_tool", side_effect=lambda x, y: y), \
                 patch.object(splits.guard, "_run", side_effect=lambda argv: good if "badging" in argv else bad):
                with self.assertRaisesRegex(splits.SplitError, "publisher_certificate_mismatch"):
                    splits.verify_component(p, package="com.kwai.video", version=647103)

    def test_appium_canary_denied_by_default(self):
        with patch.dict(os.environ, {"SPAWNDROID_SPLIT_INSTALL_CANARY_ENABLED": "0"}):
            with self.assertRaisesRegex(splits.SplitError, "appium_canary_not_authorized"):
                splits.webdriver_script(lambda *args: self.fail("must not execute"),
                                        "com.kwai.video", 647103,
                                        [x["url"] for x in example()["files"]])
        print("KWAI_SPLITS_DEFAULT_NO_ANDROID_SESSION=PASS")

    def test_webdriver_invokes_multiple_apks_only(self):
        calls = []
        def execute(script, args):
            calls.append((script, args))
            if script == "mobile: isAppInstalled":
                return True
            if script == "mobile: listApps":
                return {"com.kwai.video": {"versionCode": 647103}}
            return None
        urls = [x["url"] for x in splits.validate_manifest(example(), SOURCE)["files"]]
        with patch.dict(os.environ, {"SPAWNDROID_SPLIT_INSTALL_CANARY_ENABLED": "1"}):
            receipt = splits.webdriver_script(execute, "com.kwai.video", 647103, urls)
        self.assertEqual(calls[0][0], "mobile: installMultipleApks")
        self.assertFalse(calls[0][1]["options"]["replace"])
        self.assertEqual([x[0] for x in calls],
                         ["mobile: installMultipleApks", "mobile: isAppInstalled", "mobile: listApps"])
        self.assertFalse(receipt["provider_session_closed"])
        self.assertFalse(receipt["publication_attempted"])
        print("KWAI_SPLITS_APPIUM_W3C_CONTRACT=PASS")

    def test_webdriver_unverified_version_fails_closed(self):
        def execute(script, args):
            if script == "mobile: listApps":
                return {"com.kwai.video": {"versionCode": 1}}
            return True
        with patch.dict(os.environ, {"SPAWNDROID_SPLIT_INSTALL_CANARY_ENABLED": "1"}):
            with self.assertRaisesRegex(splits.SplitError, "remote_version_unverified"):
                splits.webdriver_script(execute, "com.kwai.video", 647103,
                                        [x["url"] for x in example()["files"]])

    def test_missing_installed_package_fails_closed(self):
        def execute(script, args):
            return False
        with patch.dict(os.environ, {"SPAWNDROID_SPLIT_INSTALL_CANARY_ENABLED": "1"}):
            with self.assertRaisesRegex(splits.SplitError, "remote_install_not_confirmed"):
                splits.webdriver_script(execute, "com.kwai.video", 647103,
                                        [x["url"] for x in example()["files"]])


if __name__ == "__main__":
    unittest.main()
