#!/usr/bin/env python3
"""Cloud-only TikTok @lucasrosalem4 publisher.

Reads an encrypted GitHub Actions secret in memory and uses an independent
Neon OIDC-fenced queue. A video can start only after its durable Neon STARTED
checkpoint; uncertain posts are never retried without independent evidence.
The separate Windows scheduler must be disabled before enabling cloud writes.
"""
from __future__ import annotations
import base64,hashlib,json,os,re,sys,tempfile,time,urllib.error,urllib.parse,urllib.request,zlib
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"direct-tiktok-publisher"))
import tiktok_web_publish as t

ACCOUNT="lucasrosalem4"
QUEUE="https://br-crimson-unit-b89nau08-cortestiktok4.compute.c-14.us-east-1.aws.neon.tech/"
BACKUP_QUEUE="https://anthares-cortes-tiktok-lucas4-ha.anthares1.workers.dev/"
AUDIENCE="https://anthares-remote-primary.vercel.app/api/cortes-tiktok"
SEGMENT=re.compile(r"^g\d+:[A-Za-z0-9_-]{6,60}:\d+:\d+$")
VID=re.compile(r"^\d{12,25}$")


class SafeStop(Exception):
    pass


def read_json(response):
    if "json" not in str(response.headers.get("Content-Type") or "").lower():
        raise SafeStop("UNEXPECTED_JSON_RESPONSE_CONTENT_TYPE")
    obj=json.load(response)
    if not isinstance(obj,dict):
        raise SafeStop("INVALID_JSON_RESPONSE")
    return obj


def oidc():
    url=os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL","")
    secret=os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN","")
    if not url or not secret or os.environ.get("GITHUB_REF")!="refs/heads/main":
        raise SafeStop("GITHUB_ACTIONS_MAIN_OIDC_UNAVAILABLE")
    address=url+("&" if "?" in url else "?")+urllib.parse.urlencode({"audience":AUDIENCE})
    request=urllib.request.Request(address,headers={"Authorization":"Bearer "+secret,"Accept":"application/json"})
    for index in range(4):
        try:
            with urllib.request.urlopen(request,timeout=24) as resp:
                jwt=str(read_json(resp).get("value") or "")
            if not 200<=len(jwt)<=16000:
                raise SafeStop("OIDC_TOKEN_VALUE_INVALID")
            return jwt
        except urllib.error.HTTPError as e:
            if e.code not in (500,502,503,504) or index==3:
                raise
        except (TimeoutError,urllib.error.URLError,OSError):
            if index==3:
                raise
        time.sleep((2,5,10)[index])
    raise SafeStop("OIDC_RETRY_EXHAUSTED")


def call(action,token,payload=None):
    url=QUEUE+"?"+urllib.parse.urlencode({"action":action})
    headers={"Accept":"application/json","Authorization":"Bearer "+token}
    if payload is not None:
        headers["Content-Type"]="application/json"
    request=urllib.request.Request(url,
        data=json.dumps(payload,separators=(",",":")).encode() if payload is not None else None,
        headers=headers,method="POST" if payload is not None else "GET")
    with urllib.request.urlopen(request,timeout=35) as resp:
        out=read_json(resp)
    if not out.get("ok"):
        raise SafeStop("NEON_ACTION_NOT_ACKNOWLEDGED_"+action)
    return out


def state_from_secret():
    raw=os.environ.get("TIKTOK_LUCASROSALEM4_STORAGE_STATE","")
    if not raw or len(raw)>48000:
        raise SafeStop("SECONDARY_SECRET_NOT_BOUND_OR_TOO_LARGE")
    try:
        decoded=zlib.decompress(base64.b64decode(raw,validate=True))
        if len(decoded)>600000:
            raise SafeStop("SECONDARY_SECRET_SIZE_LIMIT")
        state=json.loads(decoded)
    except (ValueError,zlib.error,TypeError) as e:
        raise SafeStop("SECONDARY_SECRET_DECOMPRESSION_INVALID") from e
    if not isinstance(state,dict) or not isinstance(state.get("cookies"),list):
        raise SafeStop("SECONDARY_SESSION_FORMAT_INVALID")
    cookies=state["cookies"]
    authenticated=[c for c in cookies if
        c.get("name") in ("sessionid","sessionid_ss","sid_tt") and
        "tiktok.com" in str(c.get("domain","")) and
        (float(c.get("expires",0))<=0 or float(c.get("expires"))>time.time())]
    if not authenticated:
        raise SafeStop("SECONDARY_SESSION_EXPIRED")
    return state


def studio(page):
    response=page.goto("https://www.tiktok.com/tiktokstudio/content",wait_until="domcontentloaded",timeout=50000)
    page.wait_for_timeout(3000)
    if response is None or response.status>=400 or urlparse(page.url).hostname not in ("www.tiktok.com","tiktok.com"):
        raise SafeStop("SECONDARY_STUDIO_HTTP_BLOCKED")
    if "/login" in page.url.lower() or page.locator('input[type=password]').count()>0:
        raise SafeStop("SECONDARY_STUDIO_LOGIN_REQUIRED")
    links=page.locator('a[href*="/@"]').evaluate_all(
        "(xs)=>xs.filter(x=>/\/video\/[0-9]+/.test(x.href)).map(x=>({href:x.href,text:(x.innerText||x.getAttribute('aria-label')||'').slice(0,700)})).slice(0,100)")
    author=set()
    records={}
    for item in links:
        match=re.search(r"/@([^/]+)/video/(\d{12,25})",str(item.get("href") or ""))
        if match:
            author.add(match.group(1).casefold())
            if item.get("text"):
                records[match.group(2)]=str(item["text"])
    if author!={ACCOUNT}:
        raise SafeStop("SECONDARY_STUDIO_IDENTITY_NOT_EXACT")
    return records


def marker(sid):
    return "#anthares"+hashlib.sha256((ACCOUNT+":"+sid).encode()).hexdigest()[:10]


def preflight_media(job,directory):
    address=str(job.get("media_url") or "")
    url=urlparse(address)
    if url.scheme!="https" or url.hostname not in ("anthares.us","www.anthares.us") or url.username or url.password:
        raise SafeStop("SECONDARY_MEDIA_ORIGIN_INVALID")
    request=urllib.request.Request(address,headers={"Accept":"video/mp4"})
    with urllib.request.urlopen(request,timeout=45) as response:
        if response.status!=200 or "video" not in response.headers.get("Content-Type",""):
            raise SafeStop("SECONDARY_MEDIA_HTTP_NOT_VIDEO")
        size_limit=150*1024*1024
        data=response.read(size_limit+1)
    if not 32768<=len(data)<=size_limit:
        raise SafeStop("SECONDARY_MEDIA_SIZE_INVALID")
    path=directory/"short.mp4"
    path.write_bytes(data)
    return path


def caption_for(job):
    title=" ".join(str(job.get("title") or "").split()).replace("● Universo Anthares","").strip()[:125]
    if len(title)<8:
        raise SafeStop("SECONDARY_TITLE_NOT_VALID")
    return title+" #BookTokBrasil #Literatura #UniversoAnthares "+marker(job["segment_id"])


def fill_caption(page,caption):
    target=marker_from_caption(caption)
    for css in ('[contenteditable="true"][data-e2e*="caption"]','div[contenteditable="true"]','[role="textbox"]','textarea'):
        elems=page.locator(css)
        for index in range(min(12,elems.count())):
            el=elems.nth(index)
            try:
                if not el.is_visible(timeout=900):
                    continue
                el.fill(caption,timeout=8000)
                current=el.inner_text(timeout=2300) if el.get_attribute("contenteditable")=="true" else el.input_value(timeout=2300)
                if target in current.casefold() and caption[:23].casefold() in current.casefold():
                    return
            except Exception:
                continue
    raise SafeStop("SECONDARY_CAPTION_UNVERIFIED")


def marker_from_caption(value):
    found=re.search(r"#anthares[a-f0-9]{10}",value,re.I)
    if not found:
        raise SafeStop("SECONDARY_MARKER_REQUIRED")
    return found.group(0).casefold()


def close_editor_modals(page):
    t.handle_auto_checks_modal(page)
    for label in ("Entendi","Got it"):
        try:
            button=page.get_by_role("button",name=label,exact=True).first
            if button.is_visible(timeout=850):
                button.click(timeout=9000)
                page.wait_for_timeout(700)
                break
        except Exception:
            pass


def publish_one(job,token,state):
    sid=str(job.get("segment_id") or "")
    if not SEGMENT.fullmatch(sid):
        raise SafeStop("SECONDARY_SEGMENT_ID_INVALID")
    generation=int(job.get("lease_generation") or 0)
    job_id=str(job.get("id") or "")
    if not generation or not job_id:
        raise SafeStop("SECONDARY_LEASE_FENCE_MISSING")
    from playwright.sync_api import sync_playwright
    with tempfile.TemporaryDirectory(prefix="cortes-tiktok-lucas4-") as tmp:
        media=preflight_media(job,Path(tmp))
        # The local session and the cloud secret must never be used concurrently
        # for irreversible actions. Workflow enabled only after local cutover.
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage","--disable-gpu"])
            try:
                ctx=browser.new_context(storage_state=state,locale="pt-BR",viewport={"width":1440,"height":1000})
                page=ctx.new_page()
                try:
                    previous=studio(page)
                    target=marker(sid)
                    exact=[id for id,label in previous.items() if target.casefold() in label.casefold()]
                    if len(exact)>1:
                        raise SafeStop("SECONDARY_EXISTING_POST_AMBIGUOUS")
                    # If already published, fence and reconcile only.
                    if len(exact)==1:
                        start=call("start",token,{"id":job_id,"lease_generation":generation})
                        if start.get("job",{}).get("status")!="started":
                            raise SafeStop("SECONDARY_RECONCILE_START_NOT_FENCED")
                        confirm=call("confirm",token,{"id":job_id,"lease_generation":generation,"remote_id":exact[0]})
                        if not confirm.get("job",{}).get("remote_id"):
                            raise SafeStop("SECONDARY_EXISTING_POST_CONFIRM_NOT_ACKNOWLEDGED")
                        print("SECONDARY_CLOUD_RECONCILED=https://www.tiktok.com/@"+ACCOUNT+"/video/"+exact[0],flush=True)
                        return
                    os.environ["TIKTOK_STORAGE_STATE"]=json.dumps(state,separators=(",",":"))
                    import tiktok_worker as tw
                    tw.STORAGE_RAW=os.environ["TIKTOK_STORAGE_STATE"]
                    tw.EXPECTED_USERNAME=ACCOUNT
                    upload=t.open_upload(page,ctx)
                    upload.set_input_files(str(media))
                    button=t.wait_upload_ready(page,timeout_seconds=260)
                    close_editor_modals(page)
                    fill_caption(page,caption_for(job))
                    if t.set_public_visibility(page) is not True:
                        raise SafeStop("SECONDARY_VISIBILITY_NOT_PUBLIC")
                    button=t.enabled_post_button(page)
                    if button is None or not button.is_enabled():
                        raise SafeStop("SECONDARY_POST_BUTTON_NOT_READY")
                    button.scroll_into_view_if_needed(timeout=15000)
                    button.click(trial=True,timeout=13000)
                    before_url=page.url
                    # The irreversible checkpoint is persisted by the Neon
                    # server with account-specific daily budget trigger.
                    result=call("start",token,{"id":job_id,"lease_generation":generation})
                    if result.get("job",{}).get("status")!="started":
                        raise SafeStop("SECONDARY_NEON_START_FENCE_NOT_ACKNOWLEDGED")
                    print("SECONDARY_CLOUD_IRREVERSIBLE_FENCE=1",flush=True)
                    button.click(timeout=25000)
                    page.wait_for_timeout(1300)
                    for label in ("Publicar agora","Publish now","Continuar publicando","Continue posting"):
                        try:
                            item=page.get_by_role("button",name=label,exact=False).first
                            if item.is_visible(timeout=750):
                                item.click(timeout=10000)
                                break
                        except Exception:
                            continue
                    if not t.wait_confirmation(page,before_url,timeout_seconds=90):
                        raise SafeStop("SECONDARY_AFTER_POST_UNCERTAIN")
                    found=None
                    for _ in range(4):
                        newest=studio(page)
                        matches=[id for id,label in newest.items()
                                 if id not in previous and target.casefold() in label.casefold()]
                        if len(matches)==1:
                            found=matches[0]
                            break
                        if len(matches)>1:
                            raise SafeStop("SECONDARY_MULTIPLE_NEW_MATCHES_RECONCILE")
                        page.wait_for_timeout(6000)
                    if not found or not VID.fullmatch(found):
                        raise SafeStop("SECONDARY_STUDIO_POST_CONFIRM_UNCERTAIN")
                    done=call("confirm",token,{"id":job_id,"lease_generation":generation,"remote_id":found})
                    if str(done.get("job",{}).get("remote_id"))!=found:
                        raise SafeStop("SECONDARY_NEON_CONFIRM_ACK_MISSING")
                    print("SECONDARY_CLOUD_CONFIRMED=https://www.tiktok.com/@"+ACCOUNT+"/video/"+found,flush=True)
                finally:
                    page.close()
                    ctx.close()
            finally:
                browser.close()


def select_queue():
    """Only choose a healthy shared Neon ledger before any mutating request."""
    global QUEUE
    for address in (QUEUE,BACKUP_QUEUE):
        try:
            with urllib.request.urlopen(address+"?action=health",timeout=18) as resp:
                response=read_json(resp)
            if response.get("ok") and response.get("account")==ACCOUNT and response.get("fencing"):
                QUEUE=address
                print("SECONDARY_CLOUD_QUEUE_BACKEND="+("edge" if address==BACKUP_QUEUE else "neon"),flush=True)
                return
        except (urllib.error.URLError,TimeoutError,OSError,ValueError):
            continue
    raise SafeStop("SECONDARY_CLOUD_ALL_QUEUE_INGRESS_DOWN")


def main():
    state=state_from_secret()
    token=oidc()
    select_queue()
    print("SECONDARY_CLOUD_QUEUE_READY=1",flush=True)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage","--disable-gpu"])
        try:
            ctx=browser.new_context(storage_state=state,locale="pt-BR")
            page=ctx.new_page()
            try:
                posts=studio(page)
                print("SECONDARY_CLOUD_IDENTITY_VERIFIED account="+ACCOUNT+" existing="+str(len(posts)),flush=True)
            finally:page.close();ctx.close()
        finally:browser.close()
    if os.environ.get("TIKTOK_LUCASROSALEM4_CLOUD_ENABLED","").lower()!="true":
        print("SECONDARY_CLOUD_STANDBY_NO_PUBLICATION=1",flush=True)
        return 0
    sync=call("mirror",token,{})
    print("SECONDARY_CLOUD_QUEUE_MIRRORED="+str(sync.get("mirrored")),flush=True)
    claimed=call("claim",token,{})
    job=claimed.get("job")
    if not job:
        print("SECONDARY_CLOUD_QUEUE_IDLE",flush=True)
        return 0
    try:
        publish_one(job,token,state)
    except Exception:
        # Lease may have reached STARTED; never automatically requeue
        # after a possible published post. Neon fail action distinguishes.
        try:
            call("fail",token,{"id":job["id"],"lease_generation":int(job["lease_generation"]),
                                "error":"secondary_cloud_requires_reconciliation"})
        except Exception:
            pass
        raise
    return 0


if __name__=="__main__":
    try:sys.exit(main())
    except SafeStop as exc:
        print("SECONDARY_CLOUD_HOLD="+str(exc)[:125],file=sys.stderr,flush=True)
        sys.exit(2)
    except Exception as exc:
        print("SECONDARY_CLOUD_ERROR="+type(exc).__name__,file=sys.stderr,flush=True)
        sys.exit(3)
