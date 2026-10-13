"""Static safety regression checks for Anthares-browser's isolated runtime."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent

class IsolationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.start = (ROOT / "start.sh").read_text()
        cls.docker = (ROOT / "Dockerfile").read_text()
        cls.api = (ROOT / "app.py").read_text()

    def test_dedicated_virtual_display(self):
        self.assertIn('Xvfb "$DISPLAY"', self.start)
        self.assertIn('export DISPLAY=', self.start)

    def test_dedicated_profile(self):
        self.assertIn('--user-data-dir="$CHROME_PROFILE_DIR"', self.start)
        self.assertIn('/data/chrome-profile', self.start)

    def test_loopback_cdp(self):
        self.assertIn('--remote-debugging-address=127.0.0.1', self.start)
        self.assertNotIn('EXPOSE 9222', self.docker)

    def test_no_host_gui_fallback(self):
        for forbidden in ('xdotool', 'pyautogui', 'Chrome\\User Data', '--remote-debugging-address=0.0.0.0'):
            self.assertNotIn(forbidden, self.start)

    def test_api_requires_token(self):
        self.assertIn('def require_token(', self.api)
        self.assertIn('Depends(require_token)', self.api)

if __name__ == "__main__":
    unittest.main()
