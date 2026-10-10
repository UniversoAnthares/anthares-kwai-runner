import unittest
from anthares_native.collector import collect

class CollectorTests(unittest.TestCase):
    def test_empty(self):
        self.assertFalse(collect("","")["identity_verified"])
    def test_identity_requires_two_signals(self):
        self.assertFalse(collect("KWAI_IDENTITY_PROFILE_MATCH=1","")["identity_verified"])
    def test_restored_needs_vault_save(self):
        e=collect("KWAI_IDENTITY_PROFILE_MATCH=1\nKWAI_SESSION_AUTHENTICATED_RESTORED","")
        self.assertTrue(e["restored_identity_verified"])
        self.assertFalse(e["encrypted_session_saved"])
    def test_video_url_requires_verified_flag(self):
        e=collect("","KWAI_PUBLIC_VIDEO_URL=https://www.kwai.com/abc")
        self.assertFalse(e["publication_verified"])
    def test_invalid_video_url(self):
        e=collect("","KWAI_PUBLIC_VIDEO_URL=https://evil.example/video\nKWAI_PUBLICATION_VERIFIED=1")
        self.assertFalse(e["publication_verified"])

if __name__=="__main__":
    unittest.main()
