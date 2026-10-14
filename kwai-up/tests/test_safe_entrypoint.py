import importlib.util
import os
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("kwai_up_safe", ROOT / "kwai_up_safe.py")
ks = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ks
SPEC.loader.exec_module(ks)
CASE = int(os.environ.get("KWAI_UP_CASE", "1"))


class TestSafeEntrypoint(unittest.TestCase):
    def test_review_pending_is_failure_not_success(self):
        samples = [
            "Enviado com sucesso, por favor aguarde a revisão",
            "enviado com sucesso por favor aguarde a revisao",
        ]
        text = samples[(CASE - 1) % len(samples)]
        self.assertIsNone(ks.ku.SUCCESS_RE.search(text))
        self.assertIsNotNone(ks.ku.FAILURE_RE.search(text))

    def test_real_success_markers(self):
        samples = ["Publicado com sucesso", "Vídeo publicado", "published", "posted"]
        self.assertIsNotNone(ks.ku.SUCCESS_RE.search(samples[(CASE - 1) % len(samples)]))

    def test_account_pattern_matches_exact_identity(self):
        account = f"lucasrosalem{CASE}"
        pattern = ks.account_pattern(account)
        self.assertIsNotNone(pattern.search("@" + account))
        self.assertIsNotNone(pattern.search(account))
        self.assertIsNone(pattern.search(account + "x"))
        self.assertIsNone(pattern.search("x" + account))

    def test_empty_account_is_refused(self):
        with self.assertRaises(ks.ku.KwaiUpError):
            ks.account_pattern(" ")

    def test_prepare_has_identity_gate(self):
        source = (ROOT / "kwai_up_safe.py").read_text(encoding="utf-8")
        start = source.index("    def prepare(self)")
        end = source.index("\n\ndef main()", start)
        body = source[start:end]
        self.assertIn("self.verify_identity()", body)
        self.assertLess(body.index("self.verify_identity()"), body.index("super().prepare()"))

    def test_auth_mode_exists(self):
        source = (ROOT / "kwai_up_safe.py").read_text(encoding="utf-8")
        self.assertIn('{"probe", "auth", "prepare", "commit", "verify"}', source)

    def test_safe_entrypoint_does_not_add_memu(self):
        source = (ROOT / "kwai_up_safe.py").read_text(encoding="utf-8").casefold()
        self.assertNotIn("memuc", source)
        self.assertNotIn("memumanage", source)


if __name__ == "__main__":
    unittest.main()
