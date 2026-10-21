import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class XRouteRegistrationTests(unittest.TestCase):
    def test_each_x_worker_has_exactly_one_post_status_route(self):
        for name in ("x_render_worker_v3.py", "x_runtime_worker.py"):
            with self.subTest(worker=name):
                source = (ROOT / "infra" / name).read_text(encoding="utf-8")
                tree = ast.parse(source)
                posts = 0
                endpoints = set()
                for node in tree.body:
                    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    for decorator in node.decorator_list:
                        if (isinstance(decorator, ast.Call)
                                and isinstance(decorator.func, ast.Attribute)
                                and isinstance(decorator.func.value, ast.Name)
                                and decorator.func.value.id == "app"):
                            endpoint = decorator.args[0].value if (
                                decorator.args and isinstance(decorator.args[0], ast.Constant)) else None
                            if endpoint == "/post-status":
                                posts += 1
                            key = (node.name, endpoint)
                            self.assertNotIn(key, endpoints)
                            endpoints.add(key)
                self.assertEqual(posts, 1, "Flask route collision would prevent Northflank boot")
                self.assertNotIn("_attempt_file(", source)
                self.assertNotIn("_attempt_path(", source)


if __name__ == "__main__":
    unittest.main()
