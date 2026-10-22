#!/usr/bin/env python3
"""Read-only Codeberg OIDC claims and isolated TikTok Studio identity diagnostic.

No token, cookie or profile content is written or printed. Fails closed if
the Codeberg workflow does not match the exact vetted main-branch identity.
"""
import base64,json,os,re,sys,urllib.parse,urllib.request,zlib,time

REPO="UniversoAnthares/anthares-kwai-runner"
EXPECTED_REF="refs/heads/main"
AUD="https://anthares-remote-primary.vercel.app/api/cortes-tiktok"

def oidc():
    url=os.getenv("ACTIONS_ID_TOKEN_REQUEST_URL","")
    credential=os.getenv("ACTIONS_ID_TOKEN_REQUEST_TOKEN","")
    if not url or not credential:raise RuntimeError("FORGEJO_OIDC_CONTEXT_MISSING")
    request=urllib.request.Request(
        url+("&" if "?" in url else "?")+urllib.parse.urlencode({"audience":AUD}),
        headers={"Authorization":"Bearer "+credential,"Accept":"application/json"})
    with urllib.request.urlopen(request,timeout=24) as r:
        if r.status!=200:raise RuntimeError("FORGEJO_OIDC_REQUEST_FAILED")
        token=json.load(r).get("value","")
    parts=token.split(".")
    if len(parts)!=3:raise RuntimeError("FORGEJO_OIDC_INVALID_JWT")
    claims=json.loads(base64.urlsafe_b64decode(parts[1]+"="*(-len(parts[1])%4)))
    allowed=("https://codeberg.org/api/actions","https://codeberg.org/api/actions/")
    if claims.get("iss") not in allowed:raise RuntimeError("FORGEJO_OIDC_ISSUER_MISMATCH")
    if claims.get("repository")!=REPO or claims.get("ref")!=EXPECTED_REF:
        raise RuntimeError("FORGEJO_OIDC_REPO_OR_REF_MISMATCH")
    if AUD not in (claims["aud"] if isinstance(claims.get("aud"),list) else [claims.get("aud")]):
        raise RuntimeError("FORGEJO_OIDC_AUDIENCE_MISMATCH")
    if not isinstance(claims.get("exp"),int) or claims["exp"]<=int(time.time()):
        raise RuntimeError("FORGEJO_OIDC_EXPIRED")
    wf=str(claims.get("workflow_ref") or "")
    if not wf.startswith(REPO+"/.forgejo/workflows/") or not wf.endswith("@"+EXPECTED_REF):
        raise RuntimeError("FORGEJO_OIDC_WORKFLOW_REF_MISMATCH")
    print("CODEBERG_OIDC_VALID_IDENTITY issuer="+claims["iss"]+" workflow="+wf.split("/")[-1]+" event="+str(claims.get("event_name")),flush=True)
    return claims

def session(account):
    key={"lucasrosalem4":"TIKTOK_LUCASROSALEM4_STORAGE_STATE",
         "universo.anthares":"TIKTOK_UNIVERSO_STORAGE_STATE"}[account]
    raw=os.getenv(key,"")
    if not 5<len(raw)<55000:raise RuntimeError("CODEBERG_ACCOUNT_SECRET_UNAVAILABLE_"+account)
    state=json.loads(zlib.decompress(base64.b64decode(raw,validate=True)))
    if not state.get("cookies"):raise RuntimeError("CODEBERG_ACCOUNT_COOKIES_UNAVAILABLE")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
        try:
            ctx=browser.new_context(storage_state=state,locale="pt-BR")
            page=ctx.new_page()
            try:
                if account=="lucasrosalem4":
                    sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","tools"))
                    from cortes_tiktok_lucasrosalem4_cloud_publish import studio
                    posts=studio(page)
                    print("CODEBERG_BROWSER_SECONDARY_OWNER_VERIFIED=1 count="+str(len(posts)),flush=True)
                else:
                    response=page.goto("https://www.tiktok.com/profile",wait_until="domcontentloaded",timeout=45000)
                    page.wait_for_timeout(1800)
                    match=re.search(r"tiktok\.com/@([^/?#]+)",page.url,re.I)
                    ident=match.group(1).lower() if match else ""
                    if response is None or response.status>=400 or ident!=account:
                        raise RuntimeError("CODEBERG_PRIMARY_STUDIO_OWNER_MISMATCH")
                    print("CODEBERG_BROWSER_PRIMARY_OWNER_VERIFIED=1",flush=True)
            finally:ctx.close()
        finally:browser.close()

if __name__=="__main__":
    try:
        oidc()
        if "--browser" in sys.argv:
            session(os.getenv("TIKTOK_ACCOUNT","lucasrosalem4"))
        print("CODEBERG_TIKTOK_OIDC_PROBE_PASS=1",flush=True)
    except Exception as exc:
        print("::error::CODEBERG_TIKTOK_OIDC_PROBE_FAILED="+type(exc).__name__+":"+str(exc)[:100],file=sys.stderr,flush=True)
        sys.exit(2)
