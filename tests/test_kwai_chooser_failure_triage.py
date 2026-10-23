#!/usr/bin/env python3
import contextlib
import io
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import kwai_chooser_failure_triage as triage


class TriageTests(unittest.TestCase):
    def test_empty_screen_is_safe(self):
        data = triage.summarize("<hierarchy><node class='android.view.View' /></hierarchy>")
        self.assertEqual(data["login_surface"], "absent")
        self.assertEqual(data["offline_hint"], 0)

    def test_network_and_continue_gate_are_aggregated(self):
        xml = """<hierarchy>
        <node resource-id='com.kwai.video:id/un_connected_network' text='No internet'
              package='com.kwai.video' class='android.webkit.WebView' clickable='true'/>
        <node resource-id='com.kwai.video:id/signin_fre_continue_button' text='Continue'/>
        </hierarchy>"""
        data = triage.summarize(xml)
        self.assertEqual(data["offline_hint"], 1)
        self.assertEqual(data["webview"], 1)
        self.assertEqual(data["continue_gate"], 1)

    def test_never_emit_raw_sensitive_ui(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "semantic-secret.xml"
            p.write_text("<hierarchy><node text='private@example.invalid' class='android.widget.TextView'/></hierarchy>")
            with patch.object(sys, "argv", ["triage", "--directory", d]), contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(triage.main(), 0)
            self.assertNotIn("private@example.invalid", out.getvalue())
            self.assertIn("KWAI_TRIAGE_RAW_UI_EXPORTED=0", out.getvalue())

    def test_credential_form_detected_without_values(self):
        xml = """<hierarchy><node class='android.widget.EditText'
            resource-id='com.kwai.video:id/login_password_input'
            text='private-secret' bounds='[0,0][100,100]'/></hierarchy>"""
        data = triage.summarize(xml)
        self.assertEqual(data["login_surface"], "form")


if __name__ == "__main__":
    unittest.main()
