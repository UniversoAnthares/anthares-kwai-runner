"""Regression guards for hidden X Windows fallback and durable one-click safety."""
import ast
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"tools"/"x_local_browser_consumer.py"
INSTALL=ROOT/"tools"/"x_install_windows_fallback.ps1"

def function(name):
    module=ast.parse(FILE.read_text(encoding="utf8"))
    match=next(x for x in module.body if isinstance(x,ast.FunctionDef) and x.name==name)
    unit=ast.Module(body=[match],type_ignores=[])
    ast.fix_missing_locations(unit)
    env={"hashlib":hashlib,"re":re,"json":json,"chr":chr}
    exec(compile(unit,str(FILE),"exec"),env)
    return env[name]

class XLocalConsumerTests(unittest.TestCase):
    def test_python_compiles(self):
        ast.parse(FILE.read_text(encoding="utf8"))

    def test_idempotency_matches_cloud_fingerprint(self):
        fp=function("fp")
        body={"source_id":"cortes-facebook-long-20261020","scan_start":0,
              "segment_start":5640,"segment_end":6240}
        raw="x|lucasyahn|cortes-facebook-long-20261020|5640.000|6240.000"
        self.assertEqual(fp(body),"x_"+hashlib.sha256(raw.encode()).hexdigest())
        with self.assertRaises(ValueError):
            fp({**body,"segment_end":5700})

    def test_json_payload_fenced_roundtrip(self):
        parser=function("parse_payload")
        payload={"platform":"x","account":"lucasyahn","caption":"Vídeo seguro"}
        fence=chr(96)*3
        issue={"body":fence+"json\n"+json.dumps(payload)+"\n"+fence}
        self.assertEqual(parser(issue),payload)

    def test_atomic_claim_must_precede_single_post_click(self):
        source=FILE.read_text(encoding="utf8")
        self.assertEqual(source.count('button.evaluate("""(element, key)'),1)
        self.assertIn('if (sent.has(key)) throw new Error("X_DUPLICATE_CLICK_BLOCKED")',source)
        self.assertIn('sent.add(key);',source)
        self.assertLess(source.index('service(token,"/claim-local"'),source.index('button.evaluate("""(element, key)'))
        self.assertLess(source.index('state(n,"SUBMISSION_STARTED"'),source.index('button.evaluate("""(element, key)'))
        self.assertIn('service(token,"/confirm-local"',source)
        self.assertIn('if old.get("status")!="NOT_FOUND"',source)

    def test_recovery_and_guardrails(self):
        source=FILE.read_text(encoding="utf8")
        self.assertIn('cloud_owns_queue()',source)
        self.assertIn('ANTHARES_X_AUTOPUBLISH',source)
        self.assertIn("time.monotonic()+1800",source)
        self.assertIn("300<=seconds<=840",source)
        self.assertIn('if phase=="SUBMISSION_STARTED"',source)
        self.assertIn('"SUBMISSION_STARTED","UNCERTAIN","CONFIRMED"',source)

    def test_hidden_scheduler_and_dpapi(self):
        script=INSTALL.read_text(encoding="utf8")
        self.assertIn("wscript.exe",script)
        self.assertIn(", 0, True",script)
        self.assertIn("ConvertFrom-SecureString",script)
        self.assertIn("ConvertTo-SecureString",script)
        self.assertIn("MultipleInstances IgnoreNew",script)
        self.assertIn("Anthares X Window Invisible Guard",script)
        self.assertIn("RepetitionInterval (New-TimeSpan -Minutes 10)",script)

if __name__=="__main__":unittest.main()
