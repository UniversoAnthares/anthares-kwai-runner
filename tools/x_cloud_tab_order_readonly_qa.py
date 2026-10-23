"""Single-use read-only live test of the X posting account + timeline proof.

No GitHub issue mutation, claim, media upload, click or X post.
"""
import os
import secrets
import sys
from playwright.sync_api import sync_playwright

sys.path.insert(0,"infra")
import anthares_runtime_browser_local as vault
from tools.x_github_anthares_browser_publisher import open_authenticated,proof


def main():
    if not os.getenv("ARA_SHARED"):
        raise RuntimeError("X_READONLY_VAULT_SECRET_MISSING")
    state=vault._vault_pull()
    if not isinstance(state,dict) or not isinstance(state.get("cookies"),list):
        raise RuntimeError("X_READONLY_VAULT_UNAVAILABLE")
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(
            headless=True,timeout=45000,args=[
                "--no-sandbox","--disable-dev-shm-usage",
                "--disable-background-networking","--mute-audio"])
        try:
            context=browser.new_context(storage_state=state,locale="pt-BR",
                viewport={"width":1365,"height":768})
            posting_page=open_authenticated(context)
            print("X_LIVE_PROOF_INITIAL_IDENTITY=PASS",flush=True)
            for attempt in range(2):
                marker="__x_qa_nonexistent_"+secrets.token_hex(14)
                result=proof(context,marker,attempts=1,verified_page=posting_page)
                if result is not None:
                    raise RuntimeError("X_READONLY_FAKE_MATCH_REJECTED")
                if len(context.pages)!=1 or context.pages[0] is not posting_page:
                    raise RuntimeError("X_READONLY_AUXILIARY_TAB_LEAK")
                print("X_LIVE_PROOF_ACCOUNT_BEFORE_TAB_"+str(attempt+1)+"=PASS",flush=True)
            print("X_LIVE_PROOF_SAFETY=PASS",flush=True)
        finally:
            browser.close()


if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        code=str(exc)
        safe=code if code.startswith("X_") and code.replace("_","").isalnum() else type(exc).__name__
        print("X_LIVE_PROOF_FAILURE_CODE="+safe,flush=True)
        raise SystemExit(2)
