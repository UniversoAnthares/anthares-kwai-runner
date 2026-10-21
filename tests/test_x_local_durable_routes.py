import ast
import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"infra"))
SOURCE=ROOT/"infra"/"x_runtime_worker.py"

def isolate(name, *, auth, payload, begin, confirm):
    tree=ast.parse(SOURCE.read_text(encoding="utf-8"))
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    node.decorator_list=[]
    unit=ast.Module(body=[node],type_ignores=[])
    ast.fix_missing_locations(unit)
    scope={"_auth_ok":lambda:auth,"request":SimpleNamespace(get_json=lambda silent=True:payload),
           "jsonify":lambda **kw:kw,"re":re,"EXPECTED":"lucasyahn",
           "durable_begin":begin,"durable_confirm":confirm,
           "verified_post_url":lambda u:u if re.fullmatch(
               r"https://x.com/lucasyahn/status/[0-9]+",u or "") else None}
    exec(compile(unit,str(SOURCE),"exec"),scope)
    return scope[name]

class XLocalDurableRoutesTest(unittest.TestCase):
    def test_unauthorized_never_claims(self):
        called=[]
        endpoint=isolate("claim_local",auth=False,payload={"account":"lucasyahn",
                         "idempotency_key":"x_"+"a"*64},begin=lambda k:called.append(k),
                         confirm=lambda *a:None)
        result,code=endpoint()
        self.assertEqual(code,401)
        self.assertEqual(called,[])

    def test_exact_account_claim_calls_atomic_ledger_once(self):
        called=[]
        key="x_"+"a"*64
        endpoint=isolate("claim_local",auth=True,payload={"account":"lucasyahn",
                         "idempotency_key":key},begin=lambda k:called.append(k),
                         confirm=lambda *a:None)
        self.assertTrue(endpoint()["claimed"])
        self.assertEqual(called,[key])

    def test_wrong_account_claim_denied(self):
        called=[]
        endpoint=isolate("claim_local",auth=True,payload={"account":"other",
                         "idempotency_key":"x_"+"a"*64},begin=lambda k:called.append(k),
                         confirm=lambda *a:None)
        result,code=endpoint()
        self.assertEqual(code,400)
        self.assertFalse(called)

    def test_confirmation_requires_real_account_url_and_video_proof(self):
        called=[]
        for payload in (
            {"account":"lucasyahn","idempotency_key":"x_"+"a"*64,
             "post_url":"https://x.com/other/status/111", "video_verified":True,"caption_verified":True},
            {"account":"lucasyahn","idempotency_key":"x_"+"a"*64,
             "post_url":"https://x.com/lucasyahn/status/111", "video_verified":False,"caption_verified":True},
        ):
            endpoint=isolate("confirm_local",auth=True,payload=payload,
                             begin=lambda k:None,confirm=lambda *a:called.append(a))
            _,code=endpoint()
            self.assertEqual(code,400)
        self.assertEqual(called,[])

    def test_confirm_marks_exact_existing_key(self):
        called=[]
        key="x_"+"b"*64
        url="https://x.com/lucasyahn/status/2109698725161631921"
        payload={"account":"lucasyahn","idempotency_key":key,
                 "post_url":url,"video_verified":True,"caption_verified":True}
        endpoint=isolate("confirm_local",auth=True,payload=payload,begin=lambda k:None,
                         confirm=lambda *a:called.append(a))
        result=endpoint()
        self.assertTrue(result["confirmed"])
        self.assertEqual(result["post_url"],url)
        self.assertEqual(len(called),1)

if __name__=="__main__":unittest.main()
