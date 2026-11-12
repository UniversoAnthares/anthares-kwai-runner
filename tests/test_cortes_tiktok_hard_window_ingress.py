from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "tools" / "cortes_tiktok_queue_consumer.py"


class TikTokIngressHardWindow(unittest.TestCase):
    def test_stale_vercel_not_used_as_backend_for_mutable_actions(self):
        tree = ast.parse(CLIENT.read_text(encoding="utf8"))
        nodes = [n for n in tree.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "BACKENDS"
                         for t in n.targets)]
        self.assertEqual(len(nodes), 1)
        names = ast.unparse(nodes[0].value)
        self.assertNotIn("QUEUE", names)
        self.assertIn("br-crimson-unit-b89nau08-cortestiktok", names)
        self.assertIn("anthares-cortes-tiktok-ha.anthares1.workers.dev", names)

    def test_oidc_audience_stays_stable(self):
        source = CLIENT.read_text(encoding="utf8")
        self.assertIn(
            'QUEUE = "https://anthares-remote-primary.vercel.app/api/cortes-tiktok"',
            source,
        )
        self.assertIn("AUDIENCE = QUEUE", source)


if __name__ == "__main__":
    unittest.main()
