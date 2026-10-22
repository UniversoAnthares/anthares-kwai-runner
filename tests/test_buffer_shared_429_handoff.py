"""Any Buffer 429 affects all its channels; daily own publisher is independent."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class SharedBufferBackoff(unittest.TestCase):
    def test_cross_network_429_and_daily_handoff(self):
        s=(ROOT/"infra/neon-cortes-queue/index.mjs").read_text(encoding="utf8")
        self.assertIn("provider IN ($1,'buffer_shared')",s)
        self.assertIn("provider='buffer_shared' AND cooldown_until>now()",s)
        self.assertIn("route_decision:blocked?'own_publisher'",s)
        self.assertIn("provider_unavailable:true,delivery_route:'own'",s)
        self.assertIn("extract(hour FROM now() AT TIME ZONE 'America/Campo_Grande')>=20",s)
        self.assertIn("BUFFER_GLOBAL_DAILY=20",s)
    def test_private_consumers_persist_rate_limit_without_tokens(self):
        for filename in ("cortes_buffer_linkedin_cloud.py","cortes_buffer_instagram_cloud.py"):
            code=(ROOT/"tools"/filename).read_text()
            self.assertIn('queue("cooldown",{"seconds":1800})',code)
            self.assertIn("BUFFER_HTTP_429",code)
        pin=(ROOT/"tools/cortes_buffer_pinterest_cloud.py").read_text()
        self.assertIn('queue("cooldown",{"seconds":1800})',pin)
if __name__=="__main__":unittest.main()
