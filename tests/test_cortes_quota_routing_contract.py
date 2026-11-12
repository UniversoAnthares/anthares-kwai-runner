"""CORTES quota scopes: adapter failover versus Instagram account-wide limit.

Static offline contract, no publishing, credentials, account changes or posts.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class QuotaRoutingContract(unittest.TestCase):
    def test_buffer_provider_429_handoffs_to_independent_publisher(self):
        neon = (ROOT / "infra/neon-cortes-queue/index.mjs").read_text("utf8")
        self.assertIn("provider='buffer_shared' AND cooldown_until>now()", neon)
        self.assertIn("route_decision:blocked?'own_publisher':'buffer_if_available'", neon)
        self.assertIn("provider_unavailable:true,delivery_route:'own'", neon)
        self.assertIn("BUFFER_GLOBAL_DAILY=20", neon)

    def test_real_instagram_meta_quota_uses_account_wide_hold(self):
        graph = (ROOT / "tools/cortes_instagram_direct_cloud.py").read_text("utf8")
        self.assertIn("QUOTA_SERVICE = \"instagram-direct-graph\"", graph)
        self.assertIn("last_error_subcode=2207042", graph)
        self.assertIn("code.group(1) == \"9\"", graph)
        self.assertIn("subcode.group(1) == \"2207042\"", graph)
        self.assertIn("hold = quota_hold_until()", graph)
        self.assertIn('IDLE_PROVIDER_QUOTA_COOLDOWN', graph)
        self.assertLess(graph.index("hold = quota_hold_until()"), graph.index('for index in range(2):'))
        self.assertIn("quota = client.get_quota()", graph)

    def test_ha_route_does_not_fallback_after_provider_denial_or_mutation(self):
        ha = (ROOT / "tools/cortes_queue_ha.py").read_text("utf8")
        self.assertIn('RETRYABLE = frozenset({"enqueue", "buffer-pending"})', ha)
        self.assertIn("HTTP 401/403/409/429 always stop", ha)
        self.assertNotIn("instagram-direct-lease", ha.split("RETRYABLE =", 1)[1].split("\n", 1)[0])


if __name__ == "__main__":
    unittest.main()
