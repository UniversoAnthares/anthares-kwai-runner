import unittest
from pathlib import Path
class Schedule(unittest.TestCase):
 def test_fast_single_instance_qa(self):
  script=(Path(__file__).resolve().parents[1]/"tools"/"install_pinterest_metadata_qa.ps1").read_text()
  self.assertIn("New-TimeSpan -Minutes 3",script)
  self.assertIn("-MultipleInstances IgnoreNew",script)
  self.assertIn("-WindowStyle Hidden",script)
  self.assertIn("-ExecutionTimeLimit (New-TimeSpan -Minutes 7)",script)
if __name__=="__main__":unittest.main()
