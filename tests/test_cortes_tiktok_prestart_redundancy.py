"""Regression: no module import failure may occur after irreversible STARTED."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class TikTokPrestartRedundancyTests(unittest.TestCase):
    def test_every_hosted_route_preflights_module_before_started(self):
        source=(ROOT/"tools"/"cortes_tiktok_hosted_publish.py").read_text(encoding="utf8")
        prep=source.index('                preflight_codeberg_publisher_import(folder,state)',source.index('def main():'))
        started=source.index('        changed=q.qcall("start",control',source.index('def main():'))
        self.assertLess(prep,started)
        self.assertNotIn('if os.getenv("FORGEJO_REPOSITORY")',source[source.index('if not matching:',source.index('def main():')):started])
        self.assertIn('preflight_error = "publisher_import_preflight_failed_before_start"',source[:started])

    def test_title_audit_uses_independent_evidence_and_refuses_markerless_confirmation(self):
        source=(ROOT/"tools"/"cortes_tiktok_uncertain_batch_audit.py").read_text(encoding="utf8")
        for phrase in ("inspect_title_candidates", "public_profile_scanned",
                       "TITLE_TIME_CANDIDATE_NEEDS_REVIEW",
                       "OCT27_START", "OCT29_END", "URL.search"):
            self.assertIn(phrase,source)
        self.assertIn('"EXACT_MATCH" if len(hits[s])==1',source)
        self.assertNotIn('"EXACT_MATCH" if candidates[s]',source)

if __name__ == "__main__":
    unittest.main()
