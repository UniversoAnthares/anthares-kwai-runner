"""Fail-closed TikTok reconciliation and safe error reporting contracts."""
import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import cortes_tiktok_queue_consumer as queue


class BrowserlessRecoveryContractTests(unittest.TestCase):
    def test_only_exact_marker_and_owned_account_prove_a_post(self):
        sid="g1:A7BsgCe3-oo:7027:7068"
        marker=queue.marker(sid)
        inventory={"ok":True,"account":"universo.anthares","items":[
            {"id":"7707808236887362823","text":"Literatura "+marker},
            {"id":"7707808236887362824","text":"Unrelated video"},
        ]}
        self.assertEqual(queue.found(inventory,sid),"7707808236887362823")
        inventory["account"]="lucasrosalem4"
        with self.assertRaises(queue.SafeStop):
            queue.found(inventory,sid)

    def test_missing_marker_cannot_prove_unpublished(self):
        sid="g1:A7BsgCe3-oo:8128:8168"
        self.assertEqual(queue.found({"ok":True,
                                     "account":"universo.anthares",
                                     "items":[]},sid),"")

    def test_duplicate_exact_markers_are_rejected(self):
        sid="g1:A7BsgCe3-oo:8128:8168"
        marker=queue.marker(sid)
        evidence={"ok":True,"account":"universo.anthares","items":[
            {"id":"7707808236887362823","text":marker},
            {"id":"7707808236887362824","text":marker}
        ]}
        with self.assertRaises(queue.SafeStop):
            queue.found(evidence,sid)

    def test_http_error_exposes_only_validated_stage(self):
        error=urllib.error.HTTPError(
            "https://example.invalid/restricted",502,"Bad Gateway",{},
            io.BytesIO(b'{"error":"post_button_disabled","stage":"caption"}'))
        with patch("urllib.request.urlopen",side_effect=error):
            with self.assertRaises(queue.SafeStop) as caught:
                queue.http("https://example.invalid/restricted")
        self.assertIn("post_button_disabled_caption",str(caught.exception))

    def test_untrusted_http_error_is_redacted(self):
        response={"error":"key_ABCDEF.secret=123","stage":"https://private/"}
        error=urllib.error.HTTPError(
            "https://example.invalid/restricted",502,"Bad Gateway",{},
            io.BytesIO(json.dumps(response).encode()))
        with patch("urllib.request.urlopen",side_effect=error):
            with self.assertRaises(queue.SafeStop) as caught:
                queue.http("https://example.invalid/restricted")
        self.assertIn("_unknown_unknown",str(caught.exception))
        self.assertNotIn("ABCDEF",str(caught.exception))

    def test_reconciliation_rotation_and_cloud_gate_present(self):
        neon=(ROOT/"infra/neon-cortes-tiktok/index.mjs").read_text(encoding="utf-8")
        hosted=(ROOT/"tools/cortes_tiktok_hosted_publish.py").read_text(encoding="utf-8")
        self.assertIn("reconcile_checked_at ASC NULLS FIRST",neon)
        self.assertIn("reconcile_attempts=reconcile_attempts+1",neon)
        self.assertIn("interval '4 hours'",neon)
        self.assertIn('"/profile-inventory-secondary"',hosted)
        self.assertIn('remote_status.get("publisher_ready")',hosted)
        self.assertIn('CORTES_TIKTOK_SECONDARY_NO_MATCH_INCOMPLETE',hosted)


if __name__=="__main__":
    unittest.main()
