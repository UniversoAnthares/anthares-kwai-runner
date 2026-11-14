"""Offline-only contract tests; no real APK is downloaded, registered, or signed."""
import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "kwai_spawndroid_apk_guard.py"
spec = importlib.util.spec_from_file_location("kwai_apk_guard", SCRIPT)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

CERT = guard.EXPECTED_CERT_SHA256
GOOD_AAPT = ("package: name='com.kwai.video' versionCode='647004' "
             "versionName='13.9.30.647004'\n"
             "native-code: 'armeabi-v7a' 'arm64-v8a'\n")
GOOD_SIGNER = (
    "Verifies\n"
    "Verified using v1 scheme (JAR signing): true\n"
    "Verified using v2 scheme (APK Signature Scheme v2): true\n"
    "Verified using v3 scheme (APK Signature Scheme v3): true\n"
    "Signer #1 certificate SHA-256 digest: " + CERT + "\n"
)


class GuardTests(unittest.TestCase):
    def make_fake_apk(self, root):
        path = Path(root) / "candidate.apk"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as z:
            z.writestr("AndroidManifest.xml", b"\x03\x00\x08\x00synthetic")
            z.writestr("classes.dex", b"dex\n035\x00placeholder")
            z.writestr("assets/payload.bin", b"x" * 1_100_000)
        return path, guard.sha256_file(path)

    def validate_with_fake_tools(self, apk, sha, *,
                                 aapt=GOOD_AAPT, signer=GOOD_SIGNER):
        def executor(argv):
            return aapt if "badging" in argv else signer
        with patch.object(guard, "_tool", side_effect=lambda *a: a[1]), \
                patch.object(guard, "_run", side_effect=executor):
            return guard.verify_apk(apk, sha)

    def test_parse_package_and_native_architecture(self):
        self.assertEqual(
            guard.parse_aapt(GOOD_AAPT),
            ("com.kwai.video", 647004, "13.9.30.647004",
             ("armeabi-v7a", "arm64-v8a")),
        )

    def test_reject_bad_aapt_format(self):
        with self.assertRaisesRegex(guard.ValidationError, "manifest_unreadable"):
            guard.parse_aapt("package: no permission")

    def test_parse_signature_verified(self):
        self.assertEqual(guard.parse_apksigner(GOOD_SIGNER), CERT)

    def test_reject_unverified_signature(self):
        s = GOOD_SIGNER.replace("v2 scheme (APK Signature Scheme v2): true",
                                "v2 scheme (APK Signature Scheme v2): false")
        s = s.replace("v3 scheme (APK Signature Scheme v3): true",
                      "v3 scheme (APK Signature Scheme v3): false")
        with self.assertRaisesRegex(guard.ValidationError, "v2_v3"):
            guard.parse_apksigner(s)

    def test_reject_multiple_signing_certificates(self):
        s = GOOD_SIGNER + "Signer #2 certificate SHA-256 digest: " + "f"*64 + "\n"
        with self.assertRaisesRegex(guard.ValidationError, "signer_count"):
            guard.parse_apksigner(s)

    def test_positive_offline_guard_synthetic_apk(self):
        with tempfile.TemporaryDirectory() as temp:
            apk, sha = self.make_fake_apk(temp)
            report = self.validate_with_fake_tools(apk, sha)
            self.assertEqual(report["package"], guard.EXPECTED_PACKAGE)
            self.assertEqual(report["versionCode"], 647004)
            self.assertEqual(report["certificate_sha256"], CERT)
            print("SPAWNDROID_APK_GUARD_SYNTHETIC_CONTRACT=PASS")

    def test_sha256_mismatch_fails_before_tools(self):
        with tempfile.TemporaryDirectory() as temp:
            apk, _ = self.make_fake_apk(temp)
            with self.assertRaisesRegex(guard.ValidationError, "sha256_mismatch"):
                guard.verify_apk(apk, "a"*64)

    def test_wrong_android_package_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            apk, sha = self.make_fake_apk(temp)
            a = GOOD_AAPT.replace("com.kwai.video", "com.kwai.kuaishou.video.live")
            with self.assertRaisesRegex(guard.ValidationError, "wrong_android_package"):
                self.validate_with_fake_tools(apk, sha, aapt=a)

    def test_old_version_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            apk, sha = self.make_fake_apk(temp)
            a = GOOD_AAPT.replace("647004", "536002")
            with self.assertRaisesRegex(guard.ValidationError, "obsolete_version"):
                self.validate_with_fake_tools(apk, sha, aapt=a)

    def test_wrong_certificate_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            apk, sha = self.make_fake_apk(temp)
            s = GOOD_SIGNER.replace(CERT, "2"*64)
            with self.assertRaisesRegex(guard.ValidationError, "certificate_mismatch"):
                self.validate_with_fake_tools(apk, sha, signer=s)

    def test_non_arm64_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            apk, sha = self.make_fake_apk(temp)
            a = GOOD_AAPT.replace("'armeabi-v7a' 'arm64-v8a'",
                                  "'armeabi-v7a'")
            with self.assertRaisesRegex(guard.ValidationError, "arm64_not_supported"):
                self.validate_with_fake_tools(apk, sha, aapt=a)

    def test_registration_disabled_by_default(self):
        with tempfile.TemporaryDirectory() as temp:
            apk, sha = self.make_fake_apk(temp)
            report = self.validate_with_fake_tools(apk, sha)
            with patch.dict(os.environ, {"SPAWNDROID_REGISTER_APPROVED": "0"}):
                with self.assertRaisesRegex(guard.ValidationError, "authorization_or_key"):
                    guard.register_verified(apk, report, key="dummy")
            print("SPAWNDROID_REGISTRATION_DEFAULT_DISABLED=PASS")

    def test_no_api_mutation_on_missing_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            apk, sha = self.make_fake_apk(temp)
            report = self.validate_with_fake_tools(apk, sha)
            with patch.dict(os.environ, {}, clear=True), \
                    patch.object(guard, "_json_api") as req:
                with self.assertRaises(guard.ValidationError):
                    guard.register_verified(apk, report, key="dummy")
                req.assert_not_called()

    def test_existing_release_not_replaced(self):
        with tempfile.TemporaryDirectory() as temp:
            apk, sha = self.make_fake_apk(temp)
            report = self.validate_with_fake_tools(apk, sha)
            existing = {"apps": [{"manifest": {"packageName": "com.kwai.video"},
                                  "versions": [{"versionCode": 647004}]}]}
            with patch.dict(os.environ, {"SPAWNDROID_REGISTER_APPROVED": "1"}), \
                    patch.object(guard, "_json_api", return_value=existing) as req:
                with self.assertRaisesRegex(guard.ValidationError, "already_registered"):
                    guard.register_verified(apk, report, key="dummy")
                self.assertEqual(req.call_count, 1)

    def test_registration_rejects_wrong_server_package(self):
        self.assertEqual(guard._server_package({"manifest": {"packageName": "wrong"}}),
                         "wrong")
        self.assertEqual(guard._server_package({"parsed": {"package": "com.kwai.video"}}),
                         "com.kwai.video")

    def test_guard_refuses_untrusted_extension(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "candidate.xapk"
            path.write_bytes(b"x" * 1_100_000)
            with self.assertRaisesRegex(guard.ValidationError, "single_apk_required"):
                guard.verify_apk(path, hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
