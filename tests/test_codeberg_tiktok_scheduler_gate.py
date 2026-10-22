import pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class CodebergTikTokSchedulerGate(unittest.TestCase):
 def test_both_accounts_require_explicit_primary_flag(self):
  for account in ("lucas4","universo"):
   raw=(ROOT/".forgejo"/"workflows"/("cortes-tiktok-"+account+"-codeberg.yml")).read_text(encoding="utf-8")
   self.assertIn("forgejo.event_name == 'schedule' && vars.TIKTOK_CODEBERG_PRIMARY == 'true'",raw)
   self.assertIn("cron: '*/12 * * * *'",raw)
   self.assertIn("cancel-in-progress: false",raw)
   self.assertIn("TIKTOK_CODEBERG_PREFLIGHT_ONLY:",raw)
if __name__=="__main__":unittest.main()
