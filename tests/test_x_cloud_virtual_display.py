import unittest
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]

class XCloudVirtualDisplayTests(unittest.TestCase):
    def test_cloud_identity_browser_is_offscreen_with_xvfb(self):
        workflow=(ROOT/".github/workflows/x-cloud-anthares-browser-proof.yml").read_text(encoding="utf8")
        cfg=yaml.safe_load(workflow)
        job=cfg["jobs"]["identity"]
        self.assertEqual(job["env"]["ANTHARES_X_VIRTUAL_DISPLAY"],"1")
        self.assertIn("xvfb-run -a python -u tools/x_cloud_browser_identity_probe.py",workflow)
        self.assertNotIn("x_github_anthares_browser_publisher.py",workflow)
        script=(ROOT/"tools/x_cloud_browser_identity_probe.py").read_text(encoding="utf8")
        self.assertIn('headless=os.getenv("ANTHARES_X_VIRTUAL_DISPLAY") != "1"',script)
if __name__=="__main__":unittest.main()
