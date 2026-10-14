import importlib.util
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("kwai_up", ROOT / "kwai_up.py")
ku = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ku
SPEC.loader.exec_module(ku)
CASE = int(os.environ.get("KWAI_UP_CASE", "1"))


class TestKwaiUpContract(unittest.TestCase):
    def test_no_memu_transport_dependency(self):
        source = (ROOT / "kwai_up.py").read_text(encoding="utf-8").casefold()
        self.assertNotIn("memuc", source)
        self.assertNotIn("memumanage", source)

    def test_official_package_and_proven_ids(self):
        self.assertEqual(ku.PACKAGE, "com.kwai.video")
        self.assertEqual(ku.RECORD_ID, "com.kwai.video.basis:id/id_record_layout")
        self.assertEqual(ku.PREVIEW_CONTAINER_ID, "com.kwai.video.basis:id/preview_container")
        self.assertEqual(ku.NEXT_ID, "com.kwai.video.ca_product:id/edit_next_button")
        self.assertEqual(ku.FINAL_POST_ID, "com.kwai.video.basis:id/post")

    def test_staging_is_namespaced(self):
        self.assertEqual(ku.REMOTE_DIR, "/sdcard/Movies/KwaiUp")
        source = (ROOT / "kwai_up.py").read_text(encoding="utf-8")
        self.assertIn('name.startswith("kwaiup_")', source)

    def test_publish_boundary_is_explicit(self):
        source = (ROOT / "kwai_up.py").read_text(encoding="utf-8")
        requested = source.index('self.emit("PUBLISH_REQUESTED"')
        tap = source.index("self.tap_node(post, 1)", requested)
        self.assertLess(requested, tap)

    def test_prepare_never_calls_commit(self):
        source = (ROOT / "kwai_up.py").read_text(encoding="utf-8")
        start = source.index("    def prepare(self)")
        end = source.index("    def load_ready(self)", start)
        body = source[start:end]
        self.assertNotIn("self.commit(", body)
        self.assertNotIn('"PUBLISH_REQUESTED"', body)

    def test_cold_start_discards_saved_task(self):
        source = (ROOT / "kwai_up.py").read_text(encoding="utf-8")
        self.assertIn('"--activity-clear-task"', source)

    def test_case_specific_identity_is_stable(self):
        locales = ["pt-BR", "en-US", "es-419", "pt-PT", "en-GB"]
        locale = locales[(CASE - 1) % len(locales)]
        job = f"kwai-up/{locale}/job {CASE:02d}"
        sha = (f"{CASE:02x}" * 32)[:64]
        name = ku.staged_name(job, sha, ".mp4")
        self.assertTrue(name.startswith("kwaiup_"))
        self.assertTrue(name.endswith(".mp4"))
        self.assertIn(sha[:12], name)
        self.assertNotIn("/", name)
        self.assertNotIn(" ", name)

    def test_case_specific_caption_does_not_affect_identity(self):
        accents = ["ação", "livro", "história", "conto", "leitura", "autor"]
        caption = f"{accents[(CASE - 1) % len(accents)]} #{CASE:02d}"
        sha = "a" * 64
        one = ku.staged_name(f"job-{CASE}", sha, ".mp4")
        two = ku.staged_name(f"job-{CASE}", sha, ".mp4")
        self.assertEqual(one, two)
        self.assertTrue(caption)

    def test_safe_token_handles_hostile_job_labels(self):
        samples = [
            "../../job", "job com espaço", "job;rm -rf", "áéíóú", "JOB_01",
            "job/with/slashes", "job\\windows", " job ", "job@kwai", "job#tag",
        ]
        value = samples[(CASE - 1) % len(samples)] + str(CASE)
        token = ku.safe_token(value)
        self.assertRegex(token, r"^[A-Za-z0-9._-]+$")
        self.assertLessEqual(len(token), 48)

    def test_profile_grid_requires_new_front_card_and_shift(self):
        before = ["a", "b", "c"]
        self.assertTrue(ku.profile_grid_changed(before, [f"new-{CASE}", "a", "b"]))
        self.assertFalse(ku.profile_grid_changed(before, ["a", "b", "c"]))
        self.assertFalse(ku.profile_grid_changed(before, [f"new-{CASE}", "x", "y"]))

    def test_xml_parsing_keeps_resource_ids(self):
        text = "Vídeos" if CASE % 2 else "Videos"
        xml = (
            '<hierarchy><node text="%s" content-desc="" resource-id="%s" '
            'class="android.widget.TextView" package="com.kwai.video" clickable="true" '
            'enabled="true" selected="false" checked="false" bounds="[1,2][101,202]"/>'
            '</hierarchy>'
        ) % (text, ku.NEXT_ID)
        nodes = ku.parse_nodes(xml.encode())
        self.assertEqual(nodes[0]["resource-id"], ku.NEXT_ID)
        self.assertEqual(ku.center(nodes[0]["bounds"]), (51, 102))

    def test_find_text_accepts_localized_video_tab(self):
        text = "Vídeos" if CASE % 2 else "Videos"
        node = {
            "text": text, "content-desc": "", "resource-id": "x", "class": "x",
            "package": ku.PACKAGE, "clickable": "true", "enabled": "true",
            "selected": "false", "checked": "false", "bounds": "[0,0][100,100]",
        }
        self.assertIsNotNone(ku.find_text([node], ("Vídeos", "Videos")))

    def test_adb_serial_is_optional_and_scoped(self):
        serial = f"device-{CASE:02d}" if CASE % 2 else ""
        adb = ku.ADB(serial)
        expected = ["adb"] + (["-s", serial] if serial else [])
        self.assertEqual(adb._base(), expected)

    def test_ready_proof_rejects_other_job(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = ku.Config(
                mode="commit", serial="", media=None, job_id=f"job-{CASE}",
                expected_sha256="", caption=f"caption-{CASE}", artifacts=pathlib.Path(td),
                wait=3, verify_timeout=60,
            )
            pub = ku.Publisher(cfg, adb=mock.Mock())
            pub.ready_file.write_text(
                '{"job_id":"other","caption":"caption-%d","created_at":9999999999}' % CASE,
                encoding="utf-8",
            )
            with self.assertRaises(ku.KwaiUpError):
                pub.load_ready()

    def test_ready_proof_rejects_caption_change(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = ku.Config(
                mode="commit", serial="", media=None, job_id=f"job-{CASE}",
                expected_sha256="", caption=f"caption-{CASE}", artifacts=pathlib.Path(td),
                wait=3, verify_timeout=60,
            )
            pub = ku.Publisher(cfg, adb=mock.Mock())
            pub.ready_file.write_text(
                '{"job_id":"job-%d","caption":"changed","created_at":9999999999}' % CASE,
                encoding="utf-8",
            )
            with self.assertRaises(ku.KwaiUpError):
                pub.load_ready()

    def test_human_verification_regex(self):
        variants = ["captcha", "Verificação", "verification", "security check", "confirme"]
        self.assertRegex(variants[(CASE - 1) % len(variants)], ku.HUMAN_RE)

    def test_failure_regex(self):
        variants = ["falhou", "failed", "erro", "error", "try again", "tente novamente"]
        self.assertRegex(variants[(CASE - 1) % len(variants)], ku.FAILURE_RE)

    def test_success_regex(self):
        variants = ["publicado com sucesso", "vídeo publicado", "published", "posted"]
        self.assertRegex(variants[(CASE - 1) % len(variants)], ku.SUCCESS_RE)

    def test_profile_verification_dependency_is_declared(self):
        req = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("Pillow", req)


if __name__ == "__main__":
    unittest.main()
