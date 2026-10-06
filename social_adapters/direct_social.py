#!/usr/bin/env python3
import json, os, sys, urllib.parse, urllib.request, urllib.error

class AdapterError(RuntimeError): pass
class AuthRequired(AdapterError): pass
class PaidApiDisabled(AdapterError): pass

def req(url, method="GET", data=None, token=None):
    body=None if data is None else urllib.parse.urlencode(data).encode()
    headers={"Accept":"application/json","User-Agent":"anthares-social-adapter/1"}
    if token: headers["Authorization"]="Bearer "+token
    if body: headers["Content-Type"]="application/x-www-form-urlencoded"
    try:
        with urllib.request.urlopen(urllib.request.Request(url,data=body,headers=headers,method=method),timeout=30) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        detail=e.read().decode(errors="replace")[:500]
        raise AdapterError(f"HTTP_{e.code}:{detail}") from e

def need(name):
    v=os.getenv(name,"").strip()
    if not v: raise AuthRequired(name)
    return v

def destination(platform, account_id):
    if platform not in {"instagram","threads","x"} or not account_id or ":" in account_id:
        raise AdapterError("invalid_destination")
    return f"{platform}:{account_id}"

def instagram(payload, publish=False):
    account=payload.get("account_id","primary"); dest=destination("instagram",account)
    token=need("META_INSTAGRAM_ACCESS_TOKEN"); uid=need("META_INSTAGRAM_USER_ID")
    media=payload.get("media_url",""); text=payload.get("text","")
    if not media: raise AdapterError("instagram_media_required")
    if not publish: return {"status":"READY","destination_key":dest}
    base=os.getenv("META_GRAPH_BASE","https://graph.instagram.com"); ver=os.getenv("META_GRAPH_VERSION","v24.0")
    is_video=payload.get("media_type","").lower()=="video"
    data={"access_token":token,"caption":text}
    data["media_type"]="REELS" if is_video else "IMAGE"
    data["video_url" if is_video else "image_url"]=media
    container=req(f"{base}/{ver}/{uid}/media","POST",data)
    cid=container.get("id")
    if not cid: raise AdapterError("instagram_container_missing")
    pub=req(f"{base}/{ver}/{uid}/media_publish","POST",{"creation_id":cid,"access_token":token})
    rid=pub.get("id")
    if not rid: raise AdapterError("instagram_remote_id_missing")
    verify=req(f"{base}/{ver}/{rid}?fields=id,permalink&access_token={urllib.parse.quote(token)}")
    if verify.get("id")!=rid: raise AdapterError("instagram_confirmation_failed")
    return {"status":"CONFIRMED","destination_key":dest,"remote_id":rid,"confirmation_evidence":{"verified_id":rid,"permalink":verify.get("permalink","")}}

def threads(payload, publish=False):
    account=payload.get("account_id","primary"); dest=destination("threads",account)
    token=need("THREADS_ACCESS_TOKEN"); uid=os.getenv("THREADS_USER_ID","me").strip() or "me"
    text=payload.get("text",""); media=payload.get("media_url","")
    if not text and not media: raise AdapterError("threads_content_required")
    if not publish: return {"status":"READY","destination_key":dest}
    base=os.getenv("THREADS_GRAPH_BASE","https://graph.threads.net"); ver=os.getenv("THREADS_GRAPH_VERSION","v1.0")
    data={"access_token":token,"text":text}
    if media:
        kind="VIDEO" if payload.get("media_type","").lower()=="video" else "IMAGE"
        data["media_type"]=kind; data["video_url" if kind=="VIDEO" else "image_url"]=media
    else: data["media_type"]="TEXT"
    c=req(f"{base}/{ver}/{uid}/threads","POST",data); cid=c.get("id")
    if not cid: raise AdapterError("threads_container_missing")
    p=req(f"{base}/{ver}/{uid}/threads_publish","POST",{"creation_id":cid,"access_token":token}); rid=p.get("id")
    if not rid: raise AdapterError("threads_remote_id_missing")
    verify=req(f"{base}/{ver}/{rid}?fields=id,permalink&access_token={urllib.parse.quote(token)}")
    if verify.get("id")!=rid: raise AdapterError("threads_confirmation_failed")
    return {"status":"CONFIRMED","destination_key":dest,"remote_id":rid,"confirmation_evidence":{"verified_id":rid,"permalink":verify.get("permalink","")}}

def x(payload, publish=False):
    account=payload.get("account_id","primary"); dest=destination("x",account)
    if os.getenv("X_ALLOW_PAID_API","")!="1": raise PaidApiDisabled("X official write API requires explicit paid-route opt-in")
    token=need("X_USER_ACCESS_TOKEN"); text=payload.get("text","")
    if not text: raise AdapterError("x_text_required")
    if not publish: return {"status":"READY","destination_key":dest}
    raw=json.dumps({"text":text}).encode()
    request=urllib.request.Request("https://api.x.com/2/tweets",data=raw,headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(request,timeout=30) as r: out=json.loads(r.read().decode())
    except urllib.error.HTTPError as e: raise AdapterError(f"HTTP_{e.code}:{e.read().decode(errors='replace')[:500]}") from e
    rid=(out.get("data") or {}).get("id")
    if not rid: raise AdapterError("x_remote_id_missing")
    verify=req(f"https://api.x.com/2/tweets/{rid}",token=token)
    if ((verify.get("data") or {}).get("id"))!=rid: raise AdapterError("x_confirmation_failed")
    return {"status":"CONFIRMED","destination_key":dest,"remote_id":rid,"confirmation_evidence":{"verified_id":rid}}

def main():
    payload=json.loads(sys.stdin.read() or "{}"); platform=payload.get("platform")
    publish=os.getenv("ANTHARES_SOCIAL_COMMIT","")=="1"
    fn={"instagram":instagram,"threads":threads,"x":x}.get(platform)
    if not fn: raise AdapterError("unsupported_platform")
    try: out=fn(payload,publish)
    except AuthRequired as e: out={"status":"AUTH_REQUIRED","destination_key":destination(platform,payload.get("account_id","primary")),"missing":str(e)}
    except PaidApiDisabled as e: out={"status":"BLOCKED_PAID_API","destination_key":destination(platform,payload.get("account_id","primary")),"reason":str(e)}
    print(json.dumps(out,separators=(",",":")))
if __name__=="__main__": main()
