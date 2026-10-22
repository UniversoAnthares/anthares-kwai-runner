import unittest
from pathlib import Path

class SafeFailureSite(unittest.TestCase):
    def test_does_not_dump_api_errors_or_tokens(self):
        src=(Path(__file__).resolve().parents[1]/"tools"/"cortes_buffer_pinterest_cloud.py").read_text(encoding="utf8")
        self.assertIn('Path(end.filename).name+":"+str(end.lineno)',src)
        self.assertIn('"failure_site":site',src)
        self.assertIn('if isinstance(e,ValueError) and safe.startswith("CORTES_QUEUE_"):',src)
        self.assertNotIn('"error_detail":str(e)',src)
if __name__=="__main__":unittest.main()
