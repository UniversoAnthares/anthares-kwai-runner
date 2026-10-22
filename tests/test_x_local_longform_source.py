import ast
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"tools/x_local_longform_producer.py"
INSTALL=ROOT/"tools/x_install_windows_source_fallback.ps1"
spec=importlib.util.spec_from_file_location("x_local_longform_producer",SCRIPT)
producer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(producer)


class XLocalLongformSourceTests(unittest.TestCase):
    def test_valid_python_and_hidden_installer(self):
        ast.parse(SCRIPT.read_text(encoding="utf8"))
        sh=INSTALL.read_text(encoding="utf8")
        self.assertIn("wscript.exe",sh)
        self.assertIn(", 0, True",sh)
        self.assertIn("MultipleInstances IgnoreNew",sh)
        self.assertIn("New-TimeSpan -Hours 2",sh)
        self.assertIn("pythonw.exe",sh)

    def test_github_cli_reads_unicode_without_windows_cp1252(self):
        source = SCRIPT.read_text(encoding="utf8")
        self.assertIn('encoding="utf-8", errors="strict"', source)
        self.assertIn("creationflags=subprocess.CREATE_NO_WINDOW", source)
        import subprocess
        with patch.object(producer.subprocess, "run", return_value=subprocess.CompletedProcess(
                args=["gh"], returncode=0, stdout='{"title":"O Homem do Elevador: aparências e compaixão"}',
                stderr="")):
            self.assertEqual(producer.gh("/issues/497")["title"].split(":")[0], "O Homem do Elevador")

    def test_source_queue_bootstraps_without_project_tools_package(self):
        source = SCRIPT.read_text(encoding="utf8")
        self.assertIn("def _issue_payload(", source)
        self.assertIn("def _verified_post_url(", source)
        self.assertNotIn("from tools.x_publication_safety import", source)

    def test_hidden_scheduler_waits_for_full_python_producer(self):
        shell = INSTALL.read_text(encoding="utf8")
        self.assertIn("$exe='C:\\Users\\Lucas\\AppData\\Local\\Programs\\Python\\Python311\\python.exe'", shell)
        self.assertIn("& $exe -u $target *>> $log", shell)
        self.assertIn("if($LASTEXITCODE -ne 0)", shell)

    def test_authenticated_producer_no_tinyfish_or_personal_chrome(self):
        source=SCRIPT.read_text(encoding="utf8")
        self.assertIn("X_YT_COOKIE_FILE",source)
        self.assertIn("yt",source.lower())
        self.assertNotIn("tinyfish.com",source.lower())
        self.assertNotIn("cookies-from-browser",source.lower())
        self.assertIn("X_SOURCE_WINDOWS_JSON",source)
        self.assertIn("creationflags=subprocess.CREATE_NO_WINDOW",source)

    def test_queue_inventory_preserves_source_window_reservations(self):
        import datetime
        from zoneinfo import ZoneInfo
        localday=datetime.datetime.now(ZoneInfo("America/Campo_Grande"))
        iso=localday.isoformat()
        payload={
            "platform":"x","account":"lucasyahn","duration_class":"long",
            "source_id":"xcRGdBfHX0E","scan_start":600,
            "segment_start":20,"segment_end":625,
            "microedit":{"final_duration":575}
        }
        body="".join(chr(96) for _ in range(3))+"json\n"+json.dumps(payload)+"\n"+chr(96)*3
        items=[
            {"number":1,"title":"[X-PUBLISH] reserve-a","state":"closed",
             "body":body,"comments":1},
            {"number":2,"title":"[X-PUBLISH] reserve-b","state":"open",
             "body":body,"comments":0}
        ]
        snowflake = (int(localday.timestamp() * 1000) - 1288834974657) << 22
        comments=[{"user":{"login":"github-actions[bot]"},
                   "created_at":iso,
                   "body":"X_VIDEO_CONFIRMED_V1\n"+json.dumps({
                       "kind":"X_VIDEO_CONFIRMED_V1","account":"lucasyahn",
                       "video_verified":True,"post_url":"https://x.com/lucasyahn/status/"+str(snowflake)
                   })}]
        def fakegh(path,method="GET",obj=None):
            if path.startswith("/issues?"):return items
            if path.startswith("/issues/1/comments"):return comments
            raise AssertionError(path)
        with patch.object(producer,"gh",fakegh):
            pending,confirmed,windows,_=producer.queue_inventory()
        self.assertEqual(pending,1)
        self.assertEqual(confirmed,1)
        self.assertEqual(windows,{"xcRGdBfHX0E":[600]})

    def test_media_geometry_and_duration_checked(self):
        src=SCRIPT.read_text(encoding="utf8")
        self.assertIn("300 <= seconds <= 840",src)
        self.assertIn("abs(width / height - 16 / 9) < .04",src)
        self.assertIn("99_000_000",src)
        self.assertIn("X_SOURCE_WINDOW_REUSED",src)

    def test_queue_respects_quota_and_post_proof(self):
        src=SCRIPT.read_text(encoding="utf8")
        self.assertIn("queued + confirmed >= CAP",src)
        self.assertIn("github-actions[bot]",src)
        self.assertIn("X_VIDEO_CONFIRMED_V1",src)
        self.assertIn("len(open_queue)",src)


if __name__=="__main__":
    unittest.main()
