#!/usr/bin/env python3
import json, os, subprocess, sys
providers = {
 "github": os.getenv("ANTHARES_GITHUB_READ_URL","https://github.com/UniversoAnthares/anthares-kwai-runner.git"),
 "gitlab": os.getenv("ANTHARES_GITLAB_READ_URL",""),
 "codeberg": os.getenv("ANTHARES_CODEBERG_READ_URL",""),
}
branch=os.getenv("ANTHARES_COMPARE_BRANCH","main")
out={}
for name,url in providers.items():
    if not url:
        out[name]={"state":"AUTH_REQUIRED","sha":None}; continue
    try:
        p=subprocess.run(["git","ls-remote",url,f"refs/heads/{branch}"],text=True,capture_output=True,timeout=30)
        sha=p.stdout.split()[0] if p.returncode==0 and p.stdout.strip() else None
        out[name]={"state":"UP" if sha else "DOWN","sha":sha}
    except Exception:
        out[name]={"state":"DOWN","sha":None}
known=[v["sha"] for v in out.values() if v["sha"]]
same=bool(known) and len(set(known))==1 and all(v["state"]=="UP" for v in out.values())
print(json.dumps({"branch":branch,"providers":out,"all_equal":same},sort_keys=True))
sys.exit(0 if same else 2)
