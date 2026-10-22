import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/".forgejo"/"workflows"/"x-codeberg-primary.yml"

class XCodebergPep668Regression(unittest.TestCase):
    def test_no_system_python_pip_or_playwright(self):
        text=WORKFLOW.read_text(encoding="utf8")
        self.assertNotIn("\n          python -m pip install",text)
        self.assertNotIn("\n          python -m playwright install",text)
        for p in ("smoke","publisher"):
            venv=f"/tmp/anthares-x-{p}-venv"
            self.assertIn(f"python3 -m venv {venv}",text)
            self.assertIn(f"{venv}/bin/python -m pip install",text)
            self.assertIn(f"{venv}/bin/python -m playwright install chromium",text)
        self.assertIn("run: /tmp/anthares-x-publisher-venv/bin/python",text)
        self.assertIn('runs-on: codeberg-tiny',text)
        self.assertIn('runs-on: codeberg-medium',text)

if __name__=="__main__":
    unittest.main()
