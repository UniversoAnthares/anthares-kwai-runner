#!/usr/bin/env python3
"""Independent GitHub-hosted-run proof of private Cloudflare KV persistence."""
import json
import os
import urllib.error
from kwai_session_vault_client import BASE,preflight,oidc,get_json

def main():
    run_id=os.environ.get("GITHUB_RUN_ID","")
    if not run_id.isdigit() or len(run_id)<8:
        print("KWAI_VAULT_CANARY_INVALID_RUN_ID")
        return 2
    try:
        preflight()
        headers=oidc()
        url=BASE+"/kwai/session-vault-selftest"
        previous=get_json(url,headers)
        if previous.get("ok") is not True or previous.get("persistent") is not True:
            print("KWAI_VAULT_CANARY_NOT_DURABLE")
            return 1
        prior=previous.get("previous_run_id")
        if prior==run_id:
            print("KWAI_VAULT_CANARY_NOT_INDEPENDENT")
            return 1
        posted=get_json(url,headers,data=json.dumps({"run_id":run_id}).encode())
        if posted.get("stored") is not True:
            print("KWAI_VAULT_CANARY_WRITE_NOT_ACKNOWLEDGED")
            return 1
        if prior:
            print("KWAI_VAULT_CROSS_RUN_PERSISTENCE=PROVEN")
            print("KWAI_VAULT_PRIOR_RUN_ID="+str(prior))
        else:
            print("KWAI_VAULT_CROSS_RUN_PERSISTENCE=BOOTSTRAP")
        print("KWAI_VAULT_CURRENT_RUN_ID="+run_id)
        return 0
    except (OSError,ValueError,RuntimeError,urllib.error.URLError):
        print("KWAI_VAULT_CANARY_TRANSPORT_ERROR")
        return 1

if __name__=="__main__":
    raise SystemExit(main())
