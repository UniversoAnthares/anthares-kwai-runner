"""CI-only test: exercise the actual inline deployment receipt CAS source with fake HTTP 409."""
import contextlib
import io
import json
import os
import pathlib
import re
import sys
import textwrap
import unittest
from unittest import mock
import urllib.error
import urllib.request


def receipt_source():
    text=pathlib.Path(".github/workflows/cloudflare-central-deploy.yml").read_text(encoding="utf-8")
    match=re.search(r"(?m)^          python3 - \"\$status\" \"\$health\" <<'PY'\n(.*?)^          PY$",text,re.S|re.M)
    if not match:
        raise AssertionError("RECEIPT_BLOCK_MISSING")
    return textwrap.dedent(match.group(1))


class Response:
    def __init__(self, data, status=200):
        self.data=json.dumps(data).encode("utf-8")
        self.status=status
    def read(self, *_):
        return self.data
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False


class ReceiptCasTest(unittest.TestCase):
    def test_inline_source_compiles(self):
        compile(receipt_source(), "<workflow-receipt>", "exec")

    def test_fresh_sha_after_409_and_one_successful_receipt(self):
        requests=[]
        def fake_open(req, timeout=None):
            method=req.get_method()
            requests.append((method, req.data))
            if method=="GET":
                index=sum(1 for m,_ in requests if m=="GET")
                return Response({"sha":"sha-old" if index==1 else "sha-new"})
            if method=="PUT":
                index=sum(1 for m,_ in requests if m=="PUT")
                if index==1:
                    raise urllib.error.HTTPError(req.full_url,409,"Conflict",{},None)
                return Response({"content":{}},201)
            raise AssertionError("UNEXPECTED_HTTP_METHOD")
        captured=io.StringIO()
        with mock.patch.object(urllib.request,"urlopen",side_effect=fake_open),\
             mock.patch("time.sleep",return_value=None),\
             mock.patch.dict(os.environ,{"GITHUB_REPOSITORY":"UniversoAnthares/anthares-kwai-runner","GH_TOKEN":"qa-placeholder"},clear=False),\
             mock.patch.object(sys,"argv",["script","success",'{"ok":true,"version":"qa"}']),\
             contextlib.redirect_stdout(captured):
            exec(compile(receipt_source(),"<workflow-receipt>","exec"),{"__name__":"__main__"})
        puts=[json.loads(data) for method,data in requests if method=="PUT"]
        self.assertEqual(len(puts),2)
        self.assertEqual(puts[0]["sha"],"sha-old")
        self.assertEqual(puts[1]["sha"],"sha-new")
        self.assertIn("DEPLOYMENT_RECEIPT_SAVED=201",captured.getvalue())


if __name__=="__main__":
    unittest.main()
