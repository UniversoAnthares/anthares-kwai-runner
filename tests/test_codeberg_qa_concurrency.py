import pathlib
import unittest
import yaml
ROOT=pathlib.Path(__file__).resolve().parents[1]
class QAConcurrencyGuaranteeTests(unittest.TestCase):
    def test_new_push_never_cancels_running_p0_supervisor(self):
        s=(ROOT/".forgejo/workflows/codeberg-p0-publishing-watch.yml").read_text(encoding="utf8")
        y=yaml.safe_load(s)
        self.assertIs(y["concurrency"]["cancel-in-progress"],False)
        self.assertIn("Monitor TikTok and X cloud publishers",s)
        self.assertIn("workflow_dispatch:",s)
        self.assertIn("codeberg-tiny",s)
if __name__=="__main__":
    unittest.main()
