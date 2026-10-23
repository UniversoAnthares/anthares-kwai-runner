"""Safety contract for the AntharesXBridge persistent Browser Hub profile.

No Chrome launch, cookies, remote process, network, posting or ledger writes.
"""
import ast
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse

SOURCE=Path(__file__).resolve().parents[1]/"tools/x_local_browser_consumer.py"
TEXT=SOURCE.read_text(encoding="utf-8")
TREE=ast.parse(TEXT)


class Locator:
    def __init__(self,items=None):
        self.items=items or []
        self.first=self.items[0] if self.items else None
    def count(self):
        return len(self.items)
    def all(self):
        return self.items
    def all_text_contents(self):
        return self.items


class Item:
    def __init__(self,href=None,text=None):
        self.href=href
        self.text=text
    def get_attribute(self,key):
        return self.href if key=="href" else None
    def inner_text(self,**kwargs):
        return self.text or ""


class Context:
    def __init__(self,redirect=False):
        self.events=[]
        self.redirect=redirect
    def new_page(self):
        self.events.append("new_page")
        return Page(self,temporary=True)


class Page:
    def __init__(self,ctx,href=None,switcher=None,temporary=False):
        self.context=ctx
        self.ctx=ctx
        self.href=href
        self.switcher=switcher
        self.temporary=temporary
        self.url="https://x.com/home"
    def locator(self,selector):
        if selector=='a[data-testid="AppTabBar_Profile_Link"]':
            return Locator([Item(href=self.href)] if self.href else [])
        if selector=='[data-testid="SideNav_AccountSwitcher_Button"]':
            return Locator([Item(text=self.switcher)] if self.switcher is not None else [])
        if selector=="article":
            return Locator()
        return Locator()
    def goto(self,url,**kwargs):
        self.ctx.events.append("goto")
        self.url="https://x.com/unrelated" if self.ctx.redirect else url
    def wait_for_timeout(self,ms):
        self.ctx.events.append("wait")
    def close(self):
        self.ctx.events.append("close")


def functions(*names):
    nodes=[n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(nodes)==len(names)
    env={"re":re,"urlparse":urlparse}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),"<hub-contract>","exec"),env)
    return [env[name] for name in names]


class HubContract(unittest.TestCase):
    def test_profile_link_exact_account(self):
        account,=functions("account")
        account(Page(Context(),href="/lucasyahn"))
    def test_switcher_exact_account(self):
        account,=functions("account")
        account(Page(Context(),switcher="Name @lucasyahn"))
    def test_wrong_account_denied_by_profile_link(self):
        account,=functions("account")
        with self.assertRaisesRegex(RuntimeError,"WRONG_X_ACCOUNT"):
            account(Page(Context(),href="/someoneelse"))
    def test_wrong_account_denied_by_switcher(self):
        account,=functions("account")
        with self.assertRaisesRegex(RuntimeError,"WRONG_X_ACCOUNT"):
            account(Page(Context(),switcher="Name @wronguser"))
    def test_no_identity_fails_closed(self):
        account,=functions("account")
        with self.assertRaisesRegex(RuntimeError,"ACCOUNT_UNCONFIRMED"):
            account(Page(Context()))
    def test_login_route_fails_closed(self):
        account,=functions("account")
        page=Page(Context(),href="/lucasyahn")
        page.url="https://x.com/i/flow/login"
        with self.assertRaisesRegex(RuntimeError,"X_BROWSER_HUB_LOGIN_REQUIRED"):
            account(page)
    def test_evidence_auth_before_aux_tab_and_closes_it(self):
        account,evidence=functions("account","evidence")
        ctx=Context()
        main=Page(ctx,href="/lucasyahn")
        assert evidence(ctx,"synthetic caption",verified_page=main) is None
        self.assertEqual(ctx.events[0],"new_page")
        self.assertEqual(ctx.events[-1],"close")
    def test_evidence_wrong_account_never_creates_tab(self):
        account,evidence=functions("account","evidence")
        ctx=Context()
        main=Page(ctx,href="/unrelated")
        with self.assertRaisesRegex(RuntimeError,"WRONG_X_ACCOUNT"):
            evidence(ctx,"synthetic caption",verified_page=main)
        self.assertNotIn("new_page",ctx.events)
    def test_evidence_rejects_wrong_profile_url_closes_aux_tab(self):
        account,evidence=functions("account","evidence")
        ctx=Context(redirect=True)
        main=Page(ctx,href="/lucasyahn")
        with self.assertRaisesRegex(RuntimeError,"TIMELINE_PROFILE_MISMATCH"):
            evidence(ctx,"caption",verified_page=main)
        self.assertEqual(ctx.events[-1],"close")
    def test_evidence_rejects_foreign_context(self):
        account,evidence=functions("account","evidence")
        with self.assertRaisesRegex(RuntimeError,"VERIFIED_CONTEXT_REQUIRED"):
            evidence(Context(),"caption",verified_page=Page(Context(),href="/lucasyahn"))
    def test_no_cross_profile_cookie_restoration(self):
        self.assertNotIn(".clear_cookies(",TEXT)
        self.assertNotIn(".add_cookies(",TEXT)
        self.assertNotIn("._vault_pull(",TEXT)
        self.assertNotIn("_restore_only_dedicated_x_context",TEXT)
    def test_hub_profile_checked_before_cdp(self):
        one=next(node for node in TREE.body if isinstance(node,ast.FunctionDef) and node.name=="one")
        body=ast.unparse(one)
        self.assertLess(body.index("_assert_browser_hub_x_profile()"),
                        body.index("connect_over_cdp("))
        self.assertIn('http://127.0.0.1:9224',body)
        self.assertIn('verified_page=page',body)
        self.assertIn('"/claim-local"',body)
        self.assertIn('"/confirm-local"',body)


if __name__=="__main__":
    unittest.main()
