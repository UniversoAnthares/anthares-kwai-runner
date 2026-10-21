import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class XPublishedPostRegexTests(unittest.TestCase):
    def test_real_post_id_is_detected_for_both_executors(self):
        for worker in ("x_runtime_worker.py", "x_render_worker_v3.py"):
            with self.subTest(worker=worker):
                path = ROOT / "infra" / worker
                module = ast.parse(path.read_text(encoding="utf-8"))
                status_func = next(
                    x for x in module.body if isinstance(x, ast.FunctionDef)
                    and x.name == "_statuses"
                )
                regex_calls = [
                    x for x in ast.walk(status_func)
                    if isinstance(x, ast.Call)
                    and isinstance(x.func, ast.Attribute)
                    and isinstance(x.func.value, ast.Name)
                    and x.func.value.id == "re"
                    and x.func.attr == "search"
                ]
                self.assertEqual(len(regex_calls), 1)
                expr = ast.Expression(body=regex_calls[0].args[0])
                ast.fix_missing_locations(expr)
                pattern = eval(
                    compile(expr, str(path), "eval"),
                    {"re": re, "handle": "lucasyahn"},
                )
                good = "/lucasyahn/status/2109698725161631921"
                self.assertIsNotNone(re.search(pattern, good, re.I))
                self.assertIsNone(re.search(pattern, "/other/status/2109698725161631921", re.I))
                self.assertIsNone(re.search(pattern, "/lucasyahn/status/NOT_A_POST_ID", re.I))
                self.assertIsNone(re.search(pattern, "/lucasyahn/status/\\d", re.I))


if __name__ == "__main__":
    unittest.main()
