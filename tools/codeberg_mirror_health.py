#!/usr/bin/env python3
"""Read-only Codeberg mirror health check. Never handles credentials."""
import json
import os
import urllib.request
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"AntharesMirrorAudit/1.0"}),timeout=20) as r:
        return json.load(r)
api="https://codeberg.org/api/v1/repos/UniversoAnthares/anthares-kwai-runner"
repo=get(api)
branch=get(api+"/branches/main")
sha=(branch.get("commit") or {}).get("id","").lower()
expected=os.environ.get("EXPECTED_GITHUB_MAIN_SHA","").lower()
checks={"sha_match":bool(expected) and sha==expected,
        "default_branch_main":repo.get("default_branch")=="main",
        "actions_enabled":repo.get("has_actions") is True}
print("CODEBERG_MIRROR_CHECK="+json.dumps(checks,sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 2)
