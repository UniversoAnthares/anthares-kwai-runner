import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class XCodebergChromiumLibsTests(unittest.TestCase):
    def test_playwright_dependencies_installed_for_smoke_and_publisher(self):
        s=(ROOT/".forgejo/workflows/x-codeberg-primary.yml").read_text(encoding="utf-8")
        for name in ("smoke","publisher"):
            with self.subTest(job=name):
                cmd=f"/tmp/anthares-x-{name}-venv/bin/python -m playwright install --with-deps chromium"
                self.assertIn(cmd,s)

    def test_identity_requires_os_browser_libraries_too(self):
        s=(ROOT/".forgejo/workflows/x-codeberg-auth-identity.yml").read_text(encoding="utf-8")
        self.assertIn("/tmp/anthares-x-auth-venv/bin/python -m playwright install --with-deps chromium",s)
        self.assertNotIn("python -m pip install --break-system-packages",s)

if __name__=="__main__":
    unittest.main()
