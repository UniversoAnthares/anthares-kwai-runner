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
    try:
        with urllib.request.urlopen(request,timeout=105 if action=="claim" else 35) as resp:
            out=read_json(resp)
    except urllib.error.HTTPError as exc:
        # Preserve the action and HTTP code, never the private token or URL.
        # Mirror/claim are safe to retry on the shared Neon ledger:
        # mirror is ON CONFLICT DO NOTHING, claim checks active leases.
        if exc.code in (408,429,500,502,503,504) and action in ("mirror","claim"):
            alternate=BACKUP_QUEUE if QUEUE!=BACKUP_QUEUE else None
            if alternate:
                backup=urllib.request.Request(
                    alternate+"?"+urllib.parse.urlencode({"action":action}),
                    data=request.data,headers=headers,
                    method="POST" if payload is not None else "GET")
                try:
                    with urllib.request.urlopen(backup,timeout=75 if action=="claim" else 35) as resp:
                        out=read_json(resp)
                    if not out.get("ok"):
                        raise SafeStop("TIKTOK_SECONDARY_BACKUP_UNACKNOWLEDGED_"+action)
                    print("SECONDARY_CLOUD_NEON_API_FAILOVER action="+action,flush=True)
                    return out
                except (urllib.error.URLError,TimeoutError,OSError) as alt_error:
                    print("::error::CORTES_TIKTOK_LUCAS4_BOTH_INGRESS_FAILED action="+action+
                          " primary_http="+str(exc.code)+" backup="+type(alt_error).__name__,flush=True)
        raise SafeStop("SECONDARY_NEON_HTTP_"+str(exc.code)+"_ACTION_"+action) from exc
    except (TimeoutError,urllib.error.URLError) as exc:
        # No irreversible action has occurred for mirror/claim.
        # On an ambiguous claim response the shared Neon lease fence rejects
        # any competing claim; the same database serves both ingress routes.
        if action in ("mirror","claim"):
            other=BACKUP_QUEUE if QUEUE!=BACKUP_QUEUE else (
                "https://br-crimson-unit-b89nau08-cortestiktok4.compute.c-14.us-east-1.aws.neon.tech/")
            secondary=urllib.request.Request(
                other+"?"+urllib.parse.urlencode({"action":action}),
                data=request.data,headers=headers,
                method="POST" if payload is not None else "GET")
            try:
                with urllib.request.urlopen(secondary,timeout=75 if action=="claim" else 26) as resp:
                    out=read_json(resp)
                if not out.get("ok"):
                    raise SafeStop("SECONDARY_QUEUE_ALTERNATE_UNACKNOWLEDGED_"+action)
                print("CODEBERG_TIKTOK_PRESTART_NETWORK_FAILOVER="+action,flush=True)
                return out
            except (TimeoutError,urllib.error.URLError) as alt:
                raise SafeStop("SECONDARY_BOTH_INGRESS_UNAVAILABLE_"+action) from alt
        raise SafeStop("SECONDARY_NEON_NETWORK_"+type(exc).__name__+"_ACTION_"+action) from exc
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
    """Verify exact account ownership, with bounded retries for empty hydration.

    TikTok Studio may temporarily return no video anchors after navigation.
    Missing anchors are distinct from evidence of a different account. Neither
    condition authorizes posting without the exact owner check.
    """
    for attempt in range(3):
        try:
            response=page.goto("https://www.tiktok.com/tiktokstudio/content",
                               wait_until="domcontentloaded",timeout=50000)
            page.wait_for_timeout(1800+attempt*1600)
            if (response is None or response.status>=400
                    or urlparse(page.url).hostname not in ("www.tiktok.com","tiktok.com")):
                raise SafeStop("SECONDARY_STUDIO_HTTP_BLOCKED")
            if "/login" in page.url.lower() or page.locator('input[type=password]').count()>0:
                raise SafeStop("SECONDARY_STUDIO_LOGIN_REQUIRED")
            links=page.locator('a[href*="/@"]').evaluate_all(
                "(xs)=>xs.filter(x=>/\/video\/[0-9]+/.test(x.href)).map(x=>({href:x.href,text:(x.innerText||x.getAttribute('aria-label')||'').slice(0,700)})).slice(0,100)")
            authors=set()
            records={}
            for item in links:
                match=re.search(r"/@([^/]+)/video/(\d{12,25})",str(item.get("href") or ""))
                if match:
                    authors.add(match.group(1).casefold())
                    if item.get("text"):
                        records[match.group(2)]=str(item["text"])
            if authors=={ACCOUNT}:
                return records
            if authors:
                raise SafeStop("SECONDARY_STUDIO_IDENTITY_NOT_EXACT")
            if attempt<2:
                print("SECONDARY_STUDIO_HYDRATION_RETRY="+str(attempt+1),flush=True)
                continue
            raise SafeStop("SECONDARY_STUDIO_NO_OWNED_LINKS")
        except SafeStop as exc:
            if str(exc) not in ("SECONDARY_STUDIO_HTTP_BLOCKED",):
                raise
            if attempt==2:
                raise
            print("SECONDARY_STUDIO_HTTP_RETRY="+str(attempt+1),flush=True)
    raise SafeStop("SECONDARY_STUDIO_IDENTITY_UNVERIFIED")


def marker(sid):
    return "#anthares"+hashlib.sha256((ACCOUNT+":"+sid).encode()).hexdigest()[:10]


def preflight_media(job,directory):
    """Retry only before STARTED; use the same owned official CDN fallback."""
    address=str(job.get("media_url") or "")
    url=urlparse(address)
    if url.scheme!="https" or url.hostname not in ("anthares.us","www.anthares.us") or url.username or url.password:
        raise SafeStop("SECONDARY_MEDIA_ORIGIN_INVALID")
    alt=url._replace(netloc="www.anthares.us").geturl() if url.hostname=="anthares.us" else address
    for attempt in range(3):
        current=alt if attempt==2 else address
        request=urllib.request.Request(current,headers={
            "Accept":"video/mp4,application/octet-stream",
            "User-Agent":"Mozilla/5.0 (compatible; AntharesCortes/1.0)",
        })
        try:
            with urllib.request.urlopen(request,timeout=40) as response:
                if response.status!=200:
                    raise SafeStop("SECONDARY_MEDIA_HTTP_NOT_OK")
                data=response.read(150*1024*1024+1)
            if not 32768<=len(data)<=150*1024*1024:
                raise SafeStop("SECONDARY_MEDIA_SIZE_INVALID")
            path=directory/"short.mp4"
            path.write_bytes(data)
            return path
        except urllib.error.HTTPError as exc:
            if exc.code not in (408,425,429,500,502,503,504) or attempt==2:
                raise SafeStop("SECONDARY_MEDIA_ORIGIN_HTTP_"+str(exc.code)) from exc
        except (urllib.error.URLError,OSError,TimeoutError) as exc:
            if attempt==2:
                raise SafeStop("SECONDARY_MEDIA_NETWORK_PRESTART") from exc
        print("SECONDARY_CLOUD_PREFLIGHT_RETRY attempt="+str(attempt+1),flush=True)
        time.sleep((3,8)[attempt])
    raise SafeStop("SECONDARY_MEDIA_PREFLIGHT_EXHAUSTED")


def caption_for(job):
    title=" ".join(str(job.get("title") or "").split()).replace("● Universo Anthares","").strip()[:125]
    if len(title)<8:
        raise SafeStop("SECONDARY_TITLE_NOT_VALID")
    # Preserve segment-specific tags supplied by the canonical editorial pipeline.
    # Never fabricate a topical hashtag from a title: it could misrepresent
    # the actual speech. Legacy records lacking tags retain only identity tags.
    supplied=job.get("hashtags")
    tags=[]
    if isinstance(supplied,list):
        for item in supplied:
            if isinstance(item,str) and re.fullmatch(r"#[^\\W_][\\w]*",item,re.UNICODE):
                if item.casefold() not in {x.casefold() for x in tags}:
                    tags.append(item)
    if not tags:
        print("::warning::SECONDARY_QA_EDITORIAL_CONTEXTUAL_TAGS_MISSING",flush=True)
    return title+" "+ " ".join(tags[:5]+["#UniversoAnthares",marker(job["segment_id"])])


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
    global t
    import tiktok_web_publish as t
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


def reconcile_exact_studio_match(job, token, records):
    """Read-only comparison first. Only an exact existing post may be confirmed.

    This function never calls the irreversible `start` transition, and never
    opens the upload editor for an uncertain/started record.
    """
    sid=str(job.get("segment_id") or "")
    generation=int(job.get("lease_generation") or 0)
    job_id=str(job.get("id") or "")
    if (str(job.get("status") or "") not in ("uncertain","started")
            or not SEGMENT.fullmatch(sid) or not generation or not job_id):
        raise SafeStop("SECONDARY_RECONCILIATION_FENCE_INVALID")
    target=marker(sid).casefold()
    found={str(remote_id) for remote_id,label in (records or {}).items()
           if VID.fullmatch(str(remote_id)) and target in str(label).casefold()}
    if len(found)>1:
        raise SafeStop("SECONDARY_RECONCILE_MULTIPLE_STUDIO_MATCHES")
    if not found:
        print("::warning::SECONDARY_QA_P0_UNCERTAIN_REQUIRES_STUDIO_REVIEW",flush=True)
        return False
    remote=next(iter(found))
    result=call("confirm",token,
                {"id":job_id,"lease_generation":generation,"remote_id":remote})
    if str((result.get("job") or {}).get("remote_id") or "")!=remote:
        raise SafeStop("SECONDARY_RECONCILE_CONFIRM_NOT_ACKNOWLEDGED")
    print("SECONDARY_CLOUD_RECONCILED_EXISTING="+
          "https://www.tiktok.com/@"+ACCOUNT+"/video/"+remote,flush=True)
    return True


def reconcile_uncertain(job,token,state):
    """No media upload, no POST click and no new irreversible STARTED marker."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--no-sandbox",
                                                      "--disable-dev-shm-usage","--disable-gpu"])
        try:
            ctx=browser.new_context(storage_state=state,locale="pt-BR")
            try:
                page=ctx.new_page()
                try:
                    existing=studio(page)
                except SafeStop as exc:
                    if str(exc)!="SECONDARY_STUDIO_NO_OWNED_LINKS":
                        raise
                    print("::warning::SECONDARY_QA_P0_STUDIO_HYDRATION_UNVERIFIED",flush=True)
                    return False
                except Exception as exc:
                    # Studio may time out during a read-only reconciliation.
                    # Leave the uncertain receipt untouched, notify priority QA,
                    # and allow subsequent fenced queued publications to proceed.
                    if type(exc).__name__ not in ("TimeoutError","PlaywrightTimeoutError"):
                        raise
                    print("::warning::SECONDARY_QA_P0_RECONCILIATION_TIMEOUT_PENDING",flush=True)
                    return False
                finally:
                    page.close()
            finally:
                ctx.close()
        finally:
            browser.close()
    return reconcile_exact_studio_match(job,token,existing)


def handle_claim(claimed,token,state):
    """Dispatch by Neon mode; uncertain receipts never enter publish_one."""
    mode=str(claimed.get("mode") or "")
    job=claimed.get("job")
    if mode in ("busy","idle","cap","paced") or job is None:
        print("SECONDARY_CLOUD_QUEUE_"+(mode or "IDLE").upper(),flush=True)
        return False
    if mode=="reconcile":
        return reconcile_uncertain(job,token,state)
    if mode!="publish" or str(job.get("status") or "")!="leased":
        raise SafeStop("SECONDARY_QUEUE_MODE_OR_LEASE_INVALID")
    try:
        publish_one(job,token,state)
    except Exception:
        # Pre-STARTED lease is returned to queued with bounded cooldown.
        # STARTED remains uncertain until proven remotely.
        try:
            call("fail",token,{"id":job["id"],
                "lease_generation":int(job["lease_generation"]),
                "error":"secondary_cloud_requires_reconciliation"})
        except Exception:
            pass
        raise
    return True


def select_queue():
    """Only choose a healthy shared Neon ledger before any mutating request."""
    global QUEUE
    candidates=(BACKUP_QUEUE,QUEUE) if os.getenv("FORGEJO_REPOSITORY")=="UniversoAnthares/anthares-kwai-runner" else (QUEUE,BACKUP_QUEUE)
    for address in candidates:
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
    if os.environ.get("TIKTOK_CODEBERG_PREFLIGHT_ONLY")=="1":
        status=call("status",token)
        if not status.get("ok"):
            raise SafeStop("SECONDARY_CODEBERG_OIDC_STATUS_UNVERIFIED")
        print("CODEBERG_LUCAS4_IDENTITY_AND_OIDC_VERIFIED=1",flush=True)
        return 0
    if os.environ.get("TIKTOK_LUCASROSALEM4_CLOUD_ENABLED","").lower()!="true":
        print("SECONDARY_CLOUD_STANDBY_NO_PUBLICATION=1",flush=True)
        return 0
    sync=call("mirror",token,{})
    print("SECONDARY_CLOUD_QUEUE_MIRRORED="+str(sync.get("mirrored")),flush=True)
    claimed=call("claim",token,{})
    handle_claim(claimed,token,state)
    return 0


if __name__=="__main__":
    try:sys.exit(main())
    except SafeStop as exc:
        print("SECONDARY_CLOUD_HOLD="+str(exc)[:125],file=sys.stderr,flush=True)
        sys.exit(2)
    except Exception as exc:
        print("SECONDARY_CLOUD_ERROR="+type(exc).__name__,file=sys.stderr,flush=True)
        sys.exit(3)
