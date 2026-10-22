import ast
import json
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import x_cloud_prepare as prepare

class XChronologyAndContinuityTests(unittest.TestCase):
    def test_oldest_complete_live_precedes_newer_live(self):
        # /streams order is newest to oldest, so CORTES must reverse it.
        entries=[
            {"id":"newest00001","title":"new","duration":4000,"live_status":"not_live"},
            {"id":"middle00001","title":"mid","duration":4000,"live_status":"not_live"},
            {"id":"oldest00001","title":"old","duration":4000,"live_status":"not_live"},
        ]
        class FakeYDL:
            def __init__(self,options):self.options=options
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def extract_info(self,*args,**kwargs):return {"entries":entries}
        fake=types.SimpleNamespace(YoutubeDL=FakeYDL)
        with patch.dict(sys.modules,{"yt_dlp":fake}):
            with patch.dict(os.environ,{"X_SOURCE_WINDOWS_JSON":"{}"}):
                selected=prepare.discover_source()
        self.assertEqual(selected["video_id"],"oldest00001")
        self.assertEqual(selected["scan_start"],600)

    def test_existing_earliest_live_window_keeps_chronological_cursor(self):
        entries=[
            {"id":"newest00001","title":"new","duration":4000,"live_status":"not_live"},
            {"id":"oldest00001","title":"old","duration":4000,"live_status":"not_live"},
        ]
        class FakeYDL:
            def __init__(self,options):pass
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def extract_info(self,*args,**kwargs):return {"entries":entries}
        with patch.dict(sys.modules,{"yt_dlp":types.SimpleNamespace(YoutubeDL=FakeYDL)}):
            with patch.dict(os.environ,{"X_SOURCE_WINDOWS_JSON":json.dumps({"oldest00001":[600]})}):
                selected=prepare.discover_source()
        self.assertEqual(selected["video_id"],"oldest00001")
        self.assertEqual(selected["scan_start"],1380)

    def test_self_healing_watchdog_is_hidden_and_serialized(self):
        script=(ROOT/"tools/x_windows_publication_watchdog.ps1").read_text(encoding="utf8")
        install=(ROOT/"tools/x_install_continuity_watchdog.ps1").read_text(encoding="utf8")
        self.assertIn("127.0.0.1:9224/json/version",script)
        self.assertIn("Anthares X Browser Persistent",script)
        self.assertIn("Anthares X Durable Local Standby",script)
        self.assertIn("Anthares X Longform Source Fallback",script)
        self.assertIn("DEDICATED_CHROME_RUNNING_NO_CDP",script)
        self.assertIn("MultipleInstances IgnoreNew",install)
        self.assertIn("WindowStyle Hidden",install)
        self.assertIn("RepetitionInterval (New-TimeSpan -Minutes 5)",install)

if __name__=="__main__":
    unittest.main()
