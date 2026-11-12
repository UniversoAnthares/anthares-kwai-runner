#!/usr/bin/env python3
"""Fail-closed regressions for physical Kwai PRE-COMMIT transport recovery."""
from __future__ import annotations
import ast
from pathlib import Path
import re
from types import SimpleNamespace

root=Path(__file__).resolve().parent
editor_src=(root/"kwai_native_cortes.py").read_text(encoding="utf8")
worker_src=(root/"kwai_device_failover_worker.py").read_text(encoding="utf8")
editor_tree=ast.parse(editor_src)
worker_tree=ast.parse(worker_src)
editor=next(x for x in editor_tree.body if isinstance(x,ast.FunctionDef) and x.name=="editor")
editor_code=ast.get_source_segment(editor_src,editor)
assert "android.intent.action.SEND" in editor_code
assert "intent.extra.STREAM" in editor_code
assert "'-W'" not in editor_code, "Blocking Android activity wait restored"
assert "timeout=15" in editor_code, "Async intent deadline not bounded"
assert "wait(s,RID_NEXT" in editor_code, "Mandatory editor UI verification removed"
print("ANDROID_EDITOR_ASYNC_DELIVERY_WITH_READBACK_PASS")
classifier=next(x for x in worker_tree.body if isinstance(x,ast.FunctionDef) and x.name=="classify_failure")
module=ast.Module(body=[classifier],type_ignores=[])
ns={"UNCERTAIN_PATTERNS":re.compile("UNCERTAIN|COMMITTING",re.I),
    "NON_FAILOVER_PATTERNS":re.compile("policy|privacy|copyright|content|verification|required|auth-required|identity-unverified|account|ban|rate.?limit",re.I),
    "DEVICE_PATTERNS":re.compile("adb|device offline|uiautomator|transport|timeout",re.I),
    "routing":SimpleNamespace(DEVICE_FAILURES={"device"})}
exec(compile(ast.fix_missing_locations(module),"<isolated-kwai-classifier>","exec"),ns)
cls=ns["classify_failure"]
assert cls("KWAI_PHONE_MEDIA_STAGE_PUSH_REQUIRED=1\nKWAI_UP_STATE=FAILED ERROR=timeout",75)=="device"
assert cls("KWAI_UP_STATE=FAILED ERROR=identity-unverified",79)=="platform"
assert cls("KWAI_UP_STATE=UNCERTAIN PUBLICATION_ATTEMPTED_UNVERIFIED",90)=="uncertain"
print("KWAI_PRECOMMIT_TIMEOUT_ROUTED_TO_DEVICE_BACKOFF_PASS")
print("KWAI_POSTCOMMIT_UNCERTAIN_AND_SECURITY_GATES_UNCHANGED_PASS")
