"""Contracts: Pinterest ASR QA must use the same Python 3.12 ABI in installer and task."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = (ROOT / "tools/run_pinterest_metadata_qa.ps1").read_text(encoding="utf8")
INSTALLER = (ROOT / "tools/install_pinterest_metadata_qa.ps1").read_text(encoding="utf8")


class PinterestPythonRuntime(unittest.TestCase):
    def test_wrapper_uses_pinned_python312_with_redundant_candidates(self):
        self.assertIn("$pythonCandidates=@", WRAPPER)
        self.assertIn("Python\\3.12.10\\x64\\python.exe", WRAPPER)
        self.assertIn("Python312\\python.exe", WRAPPER)
        self.assertIn("& $python -u $worker --max-clips 3", WRAPPER)
        self.assertNotIn("& py -3 $worker", WRAPPER)

    def test_install_reuses_same_abi(self):
        self.assertIn("av==17.1.0", INSTALLER)
        self.assertIn("& $python -m pip install", INSTALLER)
        self.assertIn("$pythonCandidates=@", INSTALLER)
        self.assertIn("PINTEREST_QA_PYAV_ABI_MISMATCH", WRAPPER)

    def test_installer_repairs_interactive_acl_without_full_control(self):
        self.assertIn("Get-ScheduledTask -TaskName $name", INSTALLER)
        self.assertIn(":(OI)(CI)RX", INSTALLER)
        self.assertIn("icacls.exe $qaDeps /grant $permission /T /C /Q", INSTALLER)
        self.assertNotIn(":(OI)(CI)F", INSTALLER)
        self.assertIn("New-ScheduledTaskPrincipal -UserId $user", INSTALLER)

    def test_hidden_task_and_error_reporting_remain(self):
        self.assertIn("-WindowStyle Hidden", INSTALLER)
        self.assertIn("-MultipleInstances IgnoreNew", INSTALLER)
        self.assertIn("qa-health", WRAPPER)
        self.assertIn("pinterest-qa-exit.log", WRAPPER)


if __name__ == "__main__":
    unittest.main()
