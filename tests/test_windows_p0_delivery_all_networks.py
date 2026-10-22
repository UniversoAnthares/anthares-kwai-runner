"""P0 delivery Windows task must not drop incidents from any network."""
from pathlib import Path
import unittest

SCRIPT = (Path(__file__).resolve().parents[1] / "ops/windows/cortes-p0-delivery.ps1").read_text(encoding="utf-8")

class IncidentDeliveryContract(unittest.TestCase):
    def test_every_network_is_eligible(self):
        self.assertIn("[string]::IsNullOrWhiteSpace([string]$e.network)", SCRIPT)
        self.assertNotIn("-notin @('instagram','threads')", SCRIPT)
        self.assertNotIn("$e.network -eq 'threads' -and", SCRIPT)

    def test_safety(self):
        self.assertIn("$e.priority -ne 'P0'", SCRIPT)
        self.assertIn("AddHours(-24)", SCRIPT)
        self.assertIn("Select-Object -First 8", SCRIPT)
        self.assertIn("$seen[$row.key]", SCRIPT)
        self.assertIn("load-issue-queue-auth.ps1", SCRIPT)
        self.assertIn("Remove-Item Env:", SCRIPT)

if __name__ == "__main__":
    unittest.main()
