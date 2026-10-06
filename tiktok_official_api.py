#!/usr/bin/env python3
import json, os, sys, urllib.request, urllib.parse

BASE="https://open.tiktokapis.com"
TOKEN=os.environ.get("TIKTOK_ACCESS_TOKEN","").strip()

def call(path, body=None, token=TOKEN, form=False):
    data=None
    headers={}
    if body is not None:
        if form:
            data=urllib.parse.urlencode(body).encode()
            headers["Content-Type"]="application/x-www-form-urlencoded"
        else:
            data=json.dumps(body).encode()
            headers["Content-Type"]="application/json; charset=UTF-8"
    if token: headers["Authorization"]="Bearer "+token
    req=urllib.request.Request(BASE+path,data=data,headers=headers,method="POST")
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            out=json.loads(r.read())
    except urllib.error.HTTPError as e:
        raw=e.read().decode(errors="replace")
        raise SystemExit(f"HTTP_{e.code} {raw[:1000]}")
    return out

def creator_info():
    if not TOKEN: raise SystemExit("TIKTOK_ACCESS_TOKEN_MISSING")
    out=call("/v2/post/publish/creator_info/query/",{})
    err=out.get("error",{})
    if err.get("code")!="ok": raise SystemExit("CREATOR_INFO_FAILED "+json.dumps(err))
    d=out.get("data",{})
    print("CREATOR_USERNAME="+str(d.get("creator_username","")))
    print("PRIVACY_OPTIONS="+",".join(d.get("privacy_level_options",[])))
    print("MAX_VIDEO_SEC="+str(d.get("max_video_post_duration_sec","")))
    print("SUCCESS_SIGNAL=TIKTOK_OFFICIAL_CREATOR_INFO_PROVEN")

def refresh():
    key=os.environ.get("TIKTOK_CLIENT_KEY","").strip()
    secret=os.environ.get("TIKTOK_CLIENT_SECRET","").strip()
    refresh_token=os.environ.get("TIKTOK_REFRESH_TOKEN","").strip()
    if not all((key,secret,refresh_token)): raise SystemExit("TIKTOK_REFRESH_CREDENTIALS_MISSING")
    out=call("/v2/oauth/token/",{"client_key":key,"client_secret":secret,"grant_type":"refresh_token","refresh_token":refresh_token},token="",form=True)
    # Never print token values.
    if not out.get("access_token") or not out.get("refresh_token"): raise SystemExit("TOKEN_REFRESH_FAILED")
    print("SCOPE="+str(out.get("scope","")))
    print("EXPIRES_IN="+str(out.get("expires_in","")))
    print("SUCCESS_SIGNAL=TIKTOK_OFFICIAL_REFRESH_PROVEN")

if __name__=="__main__":
    cmd=sys.argv[1] if len(sys.argv)>1 else "creator-info"
    {"creator-info":creator_info,"refresh":refresh}.get(cmd,lambda:sys.exit("UNKNOWN_COMMAND"))()
