"""The independent cloud watchdog needs today's count, not a green health ping."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class RoundHealthContract(unittest.TestCase):
    def test_read_only_neon_round_count(self):
        s=(ROOT/"infra/neon-cortes-queue/index.mjs").read_text(encoding="utf8")
        self.assertIn("request.method==='GET'&&action==='round-health'",s)
        self.assertIn("stalled_daily_round:",s)
        self.assertIn("today_master_count:",s)
        self.assertIn("America/Campo_Grande",s)
        self.assertIn("target_key='kwai:lucasrosalem'",s)
        self.assertIn("today_destinations:",s)
        self.assertNotIn("UPDATE cortes_publications",s.split("request.method==='GET'&&action==='round-health'",1)[1].split("if(request.method!=='POST')",1)[0])
if __name__=="__main__":unittest.main()
