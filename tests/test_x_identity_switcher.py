import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class _Locator:
    def __init__(self, text="", href="", present=False):
        self.text, self.href, self.present = text, href, present
        self.first = self
    def count(self):
        return int(self.present)
    def inner_text(self, timeout=None):
        return self.text
    def get_attribute(self, name):
        return self.href

class _Page:
    url = "https://x.com/home"
    def __init__(self, switcher="", profile=None):
        self.switcher = switcher
        self.profile = profile
    def goto(self, *args, **kwargs):
        pass
    def wait_for_timeout(self, value):
        pass
    def locator(self, selector):
        if selector == 'a[data-testid="AppTabBar_Profile_Link"]':
            return _Locator(href=self.profile or "", present=bool(self.profile))
        if selector == '[data-testid="SideNav_AccountSwitcher_Button"]':
            return _Locator(text=self.switcher, present=bool(self.switcher))
        raise AssertionError("Unexpected selector: " + selector)

def _identity(worker, page):
    path = ROOT / "infra" / worker
    module = ast.parse(path.read_text(encoding="utf-8"))
    node = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == "_identity")
    unit = ast.Module(body=[node],type_ignores=[])
    ast.fix_missing_locations(unit)
    scope = {"EXPECTED": "lucasyahn", "re": re}
    exec(compile(unit,str(path),"exec"),scope)
    return scope["_identity"](page)

class XIdentitySwitcherTests(unittest.TestCase):
    def test_new_x_ui_signed_in_switcher_is_verified(self):
        for file in ("x_runtime_worker.py","x_render_worker_v3.py"):
            with self.subTest(file=file):
                self.assertEqual(
                    _identity(file,_Page(switcher="Lucas Rosalem\n@lucasyahn")),
                    "lucasyahn",
                )
                self.assertEqual(_identity(file,_Page(profile="/lucasyahn")),"lucasyahn")
    def test_wrong_or_ambiguous_account_fails_closed(self):
        for file in ("x_runtime_worker.py","x_render_worker_v3.py"):
            for text in ("Another User\n@otherhandle",
                         "Accounts\n@lucasyahn\n@otherhandle",
                         "No account", "@lucasyahn_alt"):
                with self.subTest(file=file,text=text):
                    with self.assertRaisesRegex(RuntimeError,"identity mismatch"):
                        _identity(file,_Page(switcher=text))

if __name__=="__main__":
    unittest.main()
