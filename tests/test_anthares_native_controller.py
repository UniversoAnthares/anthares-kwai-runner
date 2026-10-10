import unittest
from anthares_native.controller import Evidence, Stage, advance, report

class ControllerTests(unittest.TestCase):
    def test_no_evidence_is_not_success(self):
        self.assertEqual(report(Evidence())["stage"],"needs_auth")
    def test_identity_only_is_not_persistent(self):
        self.assertEqual(advance(Stage.BOOTSTRAP,Evidence(identity_verified=True)),Stage.AUTHENTICATED)
    def test_session_saved_without_restore_is_not_persistent(self):
        self.assertEqual(advance(Stage.BOOTSTRAP,Evidence(identity_verified=True,encrypted_session_saved=True)),Stage.AUTHENTICATED)
    def test_restored_identity_required(self):
        e=Evidence(identity_verified=True,encrypted_session_saved=True,restored_identity_verified=True)
        self.assertEqual(advance(Stage.BOOTSTRAP,e),Stage.SESSION_PERSISTED)
    def test_url_without_verification_is_not_published(self):
        e=Evidence(encrypted_session_saved=True,restored_identity_verified=True,video_url="https://www.kwai.com/example")
        self.assertEqual(advance(Stage.BOOTSTRAP,e),Stage.SESSION_PERSISTED)
    def test_publication_requires_url_and_restored_identity(self):
        e=Evidence(encrypted_session_saved=True,restored_identity_verified=True,video_url="https://www.kwai.com/example",publication_verified=True)
        self.assertEqual(advance(Stage.BOOTSTRAP,e),Stage.PUBLISHED)
    def test_non_https_is_not_publication(self):
        e=Evidence(restored_identity_verified=True,video_url="file:///tmp/video",publication_verified=True)
        self.assertNotEqual(advance(Stage.BOOTSTRAP,e),Stage.PUBLISHED)

if __name__=="__main__":
    unittest.main()
