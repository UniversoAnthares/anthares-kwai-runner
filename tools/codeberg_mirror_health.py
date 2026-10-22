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
print("CODEBERG_GIT_PARITY_PROVEN="+("PASS" if checks["sha_match"] else "FAIL"))
print("CODEBERG_ACTIONS_CONFIG="+("ENABLED_RUNNER_STILL_UNVERIFIED" if checks["actions_enabled"] and checks["default_branch_main"] else "ADMIN_ACTION_REQUIRED"))
# Codeberg hosted execution is a different, separately authorized capability.
# Do not mark healthy source mirroring as failed solely due to Actions 403.
raise SystemExit(0 if checks["sha_match"] else 2)
