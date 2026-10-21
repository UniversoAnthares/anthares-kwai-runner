"""Fail-closed identity and account/slot separation in secondary TikTok login."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

SCRIPT=Path(__file__).resolve().parents[1]/"tools"/"tiktok_lucarosalem_session_capture.py"
spec=importlib.util.spec_from_file_location("tiktok_secondary_session",SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SecondaryTikTokIdentityTest(unittest.TestCase):
    def test_exact_redirect(self):
        self.assertTrue(module.verified_identity("https://www.tiktok.com/@lucarosalem", "{}"))
        self.assertFalse(module.verified_identity("https://www.tiktok.com/@universo.anthares", "{}"))
        self.assertFalse(module.verified_identity("https://www.tiktok.com/@lucasrosalem4", "{}"))
        self.assertFalse(module.verified_identity("https://evil.example/@lucarosalem", "{}"))

    def test_reject_contradictory_hydration(self):
        payload='{"__DEFAULT_SCOPE__":{"webapp.app-context":{"user":{"uniqueId":"universo.anthares"}}}}'
        self.assertFalse(module.verified_identity("https://www.tiktok.com/@lucarosalem",payload))

    def test_accept_matching_authenticated_hydration(self):
        payload='{"__DEFAULT_SCOPE__":{"webapp.app-context":{"user":{"uniqueId":"lucarosalem"}}}}'
        self.assertTrue(module.verified_identity("https://www.tiktok.com/profile",payload))
        self.assertFalse(module.verified_identity("https://www.tiktok.com/login", "{}"))

    def test_canonical_vault_unchanged_in_source(self):
        root=SCRIPT.parents[1]
        src=(root/"direct-tiktok-publisher"/"tiktok_session_authority.py").read_text(encoding="utf-8")
        assert 'browser-state/runtime' in src
        assert 'browser-state/tiktok/lucarosalem' in src
        assert "tiktok_secondary_vault_isolation_required" in src
        assert "tiktok_primary_vault_isolation_required" in src


if __name__=="__main__":
    unittest.main()
