import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class XCloudVirtualIdentityQATests(unittest.TestCase):
    def test_identity_probe_auto_triggers_and_has_p0_report(self):
        s=(ROOT/".github/workflows/x-cloud-anthares-browser-proof.yml").read_text(encoding="utf8")
        self.assertIn("branches: [main]",s)
        self.assertIn("tools/x_cloud_browser_identity_probe.py",s)
        self.assertIn("cancel-in-progress: false",s)
        self.assertIn("issues: write",s)
        self.assertIn("if: failure()",s)
        self.assertIn("issues/380/comments",s)
        self.assertIn("no_post_attempted=true",s)
        self.assertIn("xvfb-run -a python -u tools/x_cloud_browser_identity_probe.py",s)
        self.assertNotIn("tools.x_github_anthares_browser_publisher",s)
if __name__=="__main__":
    unittest.main()
