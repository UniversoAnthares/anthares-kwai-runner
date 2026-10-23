"""Hidden, serialized Windows X publication fallback. Run as interactive Lucas via pythonw.
One queued long video per invocation; Northflank cloud remains primary.
"""
import hashlib, json, os, re, subprocess, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
import requests
from playwright.sync_api import sync_playwright

REPO="UniversoAnthares/anthares-kwai-runner"
BASE="https://http--anthares-ara-northflank--6f6pbqmvhpv6.code.run/x"
ROOT=Path(r"D:\AntharsWork\x-reliability-qa-20261021")
QUEUE=ROOT/"x-local-ledger"
TZ=ZoneInfo("America/Campo_Grande")
STOP={"SUBMISSION_STARTED","UNCERTAIN","CONFIRMED","DISCARDED"}

def github(path, method="GET", body=None):
    cmd=["gh","api","repos/"+REPO+path]
    if method!="GET":cmd+=["-X",method,"--input","-"]
    result=subprocess.run(cmd,input=json.dumps(body) if body is not None else None,
                          capture_output=True,text=True,encoding="utf-8",
                          errors="strict",timeout=35)
    if result.returncode:raise RuntimeError("GITHUB_UNAVAILABLE")
    return json.loads(result.stdout) if result.stdout.strip() else {}

def parse_payload(issue):
    text=str(issue.get("body") or "")
    fence=chr(96)*3
    a=text.find(fence); b=text.rfind(fence)
    if a<0 or b<=a:raise ValueError("MISSING_JSON")
    data=text[a+3:b].strip()
    if data.lower().startswith("json"):data=data[4:].strip()
    return json.loads(data)

def fp(data):
    source=str(data.get("source_id") or "")
    lo=float(data["segment_start"])+float(data.get("scan_start") or 0)
    hi=float(data["segment_end"])+float(data.get("scan_start") or 0)
    if not source or not 300<=hi-lo<=840:raise ValueError("BAD_SEGMENT")
    raw=f"x|lucasyahn|{source}|{lo:.3f}|{hi:.3f}"
    return "x_"+hashlib.sha256(raw.encode()).hexdigest()

def listed():
    found=[]
    for page in range(1,7):
        issues=github(f"/issues?state=open&per_page=100&page={page}&sort=created&direction=asc")
        for issue in issues:
            if not str(issue.get("title") or "").startswith("[X-PUBLISH]") or issue.get("pull_request"):continue
            try:
                data=parse_payload(issue)
                if data.get("platform")!="x" or data.get("account")!="lucasyahn":continue
                if data.get("duration_class")!="long" or data.get("test_fixture"):continue
                if not 300<=float((data.get("microedit") or {}).get("final_duration") or 0)<=840:continue
                media=urlparse(str(data.get("media_url") or ""))
                if media.scheme!="https" or media.hostname!="github.com" or media.username or media.password:continue
                if not media.path.startswith("/UniversoAnthares/anthares-kwai-runner/releases/download/"):continue
                if not 0<len(str(data.get("caption") or ""))<=280:continue
                fp(data)
                date=datetime.fromisoformat(issue["created_at"].replace("Z","+00:00"))
                if date.astimezone(TZ).date()<=datetime.now(TZ).date():found.append((issue,data))
            except (ValueError,TypeError,KeyError):continue
        if len(issues)<100:break
    else:raise RuntimeError("GITHUB_QUEUE_PAGINATION")
    found.sort(key=lambda x:(0 if x[1].get("reserve_from") else 1,x[0]["created_at"]))
    return found

def logfile(issue):return QUEUE/(str(issue)+".json")
def readstate(issue):
    p=logfile(issue)
    return json.loads(p.read_text(encoding="utf8")) if p.exists() else {}
def state(issue,phase,**data):
    QUEUE.mkdir(parents=True,exist_ok=True)
    old=readstate(issue)
    value={**old,**data,"phase":phase,"updated":datetime.now(TZ).isoformat()}
    p=logfile(issue);tmp=p.with_suffix(".tmp")
    tmp.write_text(json.dumps(value,ensure_ascii=True),encoding="utf8");os.replace(tmp,p)

def auth():
    """Use the existing authenticated Windows GitHub CLI; never print token."""
    result = subprocess.run(["gh", "auth", "token"], capture_output=True,
                            text=True, timeout=20)
    token = result.stdout.strip()
    if result.returncode or len(token) < 25:
        raise RuntimeError("X_GITHUB_TOKEN_NOT_AVAILABLE")
    return token

def service(token, path, body=None):
    """Shared Neon database fence for Windows, Codeberg and cloud runners."""
    op, mark, tail = path.lstrip("/").partition("?")
    if op not in ("post-status", "claim-local", "confirm-local"):
        raise RuntimeError("X_NEON_LEDGER_BAD_OPERATION")
    url = "https://br-crimson-unit-b89nau08-xledger.compute.c-14.us-east-1.aws.neon.tech/?action=" + op + ("&" + tail if mark else "")
    try:
        r = requests.request("POST" if body is not None else "GET", url,
            json=body, headers={"Authorization":"Bearer " + token}, timeout=35)
    except requests.RequestException:
        raise RuntimeError("X_NEON_LEDGER_UNREACHABLE") from None
    if r.status_code == 409:
        raise RuntimeError("POST_ALREADY_CLAIMED")
    if r.status_code == 429:
        raise RuntimeError("DAILY_MAX_10")
    if r.status_code != 200:
        raise RuntimeError("X_NEON_LEDGER_HTTP_" + str(r.status_code))
    result = r.json()
    if result.get("ok") is not True:
        raise RuntimeError("X_NEON_LEDGER_NEGATIVE")
    return result

def cloud_owns_queue():
    """Defer to independent cloud only while a recent authenticated GH run is healthy.

    A successful GH run requires current @lucasyahn verification, including
    idle runs. Failed or delayed cloud runs release priority to Windows within
    22 minutes. PostgreSQL atomically prevents duplicates during handover.
    """
    try:
        from datetime import timezone
        # Prefer Codeberg only after an explicit authenticated-production
        # promotion. Smoke tests must never steal the Windows queue.
        try:
            # A SUCCESSFUL scheduled Codeberg publisher run proves the
            # arm gate, account, and global ledger path; skipped jobs do not.
            # Do not depend on a second GitHub configuration variable.
            resp=requests.get("https://codeberg.org/api/v1/repos/"
                "UniversoAnthares/anthares-kwai-runner/actions/runs?limit=25",
                timeout=11)
            resp.raise_for_status()
            runs=resp.json().get("workflow_runs") or []
            recent=next((run for run in runs
                if run.get("workflow_id")=="x-codeberg-primary.yml"
                and (run.get("trigger_event") or run.get("event"))=="schedule"),None)
            if recent and recent.get("status")=="success":
                stamp=datetime.fromisoformat(str(recent.get("stopped")).replace("Z","+00:00"))
                if stamp.tzinfo and 0 <= (datetime.now(timezone.utc)-stamp).total_seconds() <= 22*60:
                    return True
        except Exception:
            pass
        settings=github("/actions/variables/ANTHARES_X_AUTOPUBLISH")
        if str(settings.get("value") or "").lower() not in ("1","true"):
            return False
        data=github("/actions/workflows/x-anthares-browser-cloud-publisher.yml/runs?per_page=8")
        runs=data.get("workflow_runs") or []
        recent=next((row for row in runs if row.get("status")=="completed"),None)
        if not recent or recent.get("conclusion")!="success":
            return False
        stamped=datetime.fromisoformat(str(recent.get("updated_at") or "").replace("Z","+00:00"))
        now=datetime.now(timezone.utc)
        age=(now-stamped).total_seconds()
        return 0<=age<=22*60
    except Exception:
        return False

def path_for(issue,data):
    name=Path(urlparse(data["media_url"]).path).name
    if not re.fullmatch(r"[a-zA-Z0-9_.-]+[.]mp4",name):raise RuntimeError("UNSAFE_VIDEO_NAME")
    local=Path(r"D:\AntharsWork\cortes-facebook-long-20261020\final")/name
    if (data.get("source_id")=="cortes-facebook-long-20261020"
            and local.exists() and local.stat().st_size>100000):
        return local
    directory=ROOT/"x-longform-cache";directory.mkdir(parents=True,exist_ok=True)
    target=directory/(str(issue["number"])+"-"+name)
    if target.exists() and target.stat().st_size>100000:return target
    tmp=target.with_suffix(".part")
    try:
        with requests.get(data["media_url"],stream=True,timeout=(20,180)) as response:
            response.raise_for_status()
            if urlparse(response.url).hostname not in {"github.com","release-assets.githubusercontent.com","objects.githubusercontent.com"}:
                raise RuntimeError("UNTRUSTED_MEDIA_REDIRECT")
            length=0
            with tmp.open("wb") as dest:
                for chunk in response.iter_content(262144):
                    length+=len(chunk)
                    if length>99000000:raise RuntimeError("MEDIA_EXCEEDS_GITHUB_LIMIT")
                    dest.write(chunk)
    except requests.exceptions.HTTPError as exc:
        if getattr(exc.response,"status_code",0) not in (401,403):
            raise
        # GitHub sometimes denies anonymous release-asset redirects in the
        # dedicated Windows session. Use the already authenticated GH CLI's
        # scoped Contents access. Never retrieve tokens or use a shell.
        from tempfile import TemporaryDirectory
        media_url=urlparse(str(data["media_url"]))
        match=re.fullmatch(
            r"/UniversoAnthares/anthares-kwai-runner/releases/download/([A-Za-z0-9_.-]{1,100})/([A-Za-z0-9_.-]+[.]mp4)",
            media_url.path)
        if media_url.scheme!="https" or media_url.hostname!="github.com" or not match or match.group(2)!=name:
            raise RuntimeError("X_AUTHENTICATED_MEDIA_PATH_DENIED")
        tmp.unlink(missing_ok=True)
        with TemporaryDirectory(prefix="x-auth-media-",dir=str(directory)) as folder:
            import shutil
            cmd=["gh","release","download",match.group(1),"--repo",REPO,"--pattern",name,
                 "--dir",folder]
            env={**os.environ,"GH_PROMPT_DISABLED":"1","GIT_TERMINAL_PROMPT":"0"}
            result=subprocess.run(cmd,capture_output=True,text=True,timeout=210,
                                  env=env,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            asset=Path(folder)/name
            if result.returncode or not asset.is_file():
                raise RuntimeError("X_AUTHENTICATED_MEDIA_FALLBACK_FAILED")
            length=asset.stat().st_size
            if length>99000000:raise RuntimeError("MEDIA_EXCEEDS_GITHUB_LIMIT")
            if length<100000:raise RuntimeError("MEDIA_EMPTY")
            shutil.copyfile(asset,tmp)
    if length<100000:raise RuntimeError("MEDIA_EMPTY")
    tmp.replace(target)
    return target

def media_preflight(path):
    import shutil
    ffprobe=shutil.which("ffprobe")
    if not ffprobe:raise RuntimeError("FFPROBE_NOT_FOUND")
    run=subprocess.run([ffprobe,"-v","error","-show_entries",
                        "stream=width,height:format=duration","-of","json",str(path)],
                       capture_output=True,text=True,timeout=35)
    if run.returncode:raise RuntimeError("VIDEO_PROBE_FAILED")
    data=json.loads(run.stdout)
    video=next((r for r in data.get("streams",[]) if r.get("width")),{})
    w=int(video.get("width") or 0);h=int(video.get("height") or 0)
    seconds=float(data.get("format",{}).get("duration") or 0)
    if not (w>h>0 and abs(w/h-16/9)<0.05 and 300<=seconds<=840):
        raise RuntimeError("X_VIDEO_OUTSIDE_LONG_16_BY_9_LIMITS")

def account(page):
    # Check identity from the currently authenticated X UI, never from a
    # cookie file or the *viewed* profile URL.
    if any(path in page.url for path in (
            "/login", "/i/flow/login", "/i/jf/onboarding")):
        raise RuntimeError("X_BROWSER_HUB_LOGIN_REQUIRED")
    link=page.locator('a[data-testid="AppTabBar_Profile_Link"]')
    if link.count():
        destination=(link.first.get_attribute("href") or "").rstrip("/")
        if destination=="/lucasyahn":
            return
        if re.fullmatch(r"/[A-Za-z0-9_]{1,15}",destination):
            raise RuntimeError("WRONG_X_ACCOUNT")
    tab=page.locator('[data-testid="SideNav_AccountSwitcher_Button"]')
    if tab.count()!=1:
        raise RuntimeError("ACCOUNT_UNCONFIRMED")
    names=re.findall(r"(?<![A-Za-z0-9_])@([A-Za-z0-9_]{1,15})(?![A-Za-z0-9_])",
                     tab.first.inner_text(timeout=9000))
    if names!=["lucasyahn"]:
        raise RuntimeError("WRONG_X_ACCOUNT")


def _assert_browser_hub_x_profile():
    """Fail closed unless CDP :9224 belongs to the dedicated Hub X profile.

    Inspection only: never spawn Chrome, copy browser data, or restore cookies
    from the independent cloud vault into a persistent Hub profile.
    """
    expected=Path(r"D:\AntharsWork\browser-profiles\AntharesXBridge")
    if not expected.is_dir():
        raise RuntimeError("X_BROWSER_HUB_PROFILE_MISSING")
    query=(
        "Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | "
        "ForEach-Object { $_.CommandLine }")
    result=subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle",
         "Hidden", "-Command", query],
        capture_output=True,text=True,timeout=20,
        creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    if result.returncode:
        raise RuntimeError("X_BROWSER_HUB_PROCESS_UNVERIFIED")
    matches=[row.lower() for row in result.stdout.splitlines()
             if "--remote-debugging-port=9224" in row.lower()]
    if len(matches)!=1 or not all(marker in matches[0] for marker in (
            "--user-data-dir", "browser-profiles", "antharesxbridge")):
        raise RuntimeError("X_BROWSER_HUB_PROFILE_NOT_ISOLATED")


def _verify_existing_browser_hub_session(page):
    """Reuse Hub-owned X authentication, fail closed if it is not valid."""
    try:
        account(page)
        return
    except RuntimeError as exc:
        if str(exc) in ("WRONG_X_ACCOUNT","X_BROWSER_HUB_LOGIN_REQUIRED"):
            raise
    # React rendering can briefly hide both selectors. Retry the *same* page,
    # without loading a new route or altering the persisted browser cookies.
    deadline=time.monotonic()+15
    while time.monotonic()<deadline:
        page.wait_for_timeout(1000)
        try:
            account(page)
            return
        except RuntimeError as exc:
            if str(exc) in ("WRONG_X_ACCOUNT","X_BROWSER_HUB_LOGIN_REQUIRED"):
                raise
    raise RuntimeError("X_BROWSER_HUB_IDENTITY_UNVERIFIED")


def evidence(ctx,caption,attempts=1,verified_page=None):
    if verified_page is None or verified_page.context is not ctx:
        raise RuntimeError("X_BROWSER_HUB_VERIFIED_CONTEXT_REQUIRED")
    # Prove ownership on the Hub's signed-in tab BEFORE opening the separate
    # read-only timeline tab. Never infer identity from a viewed profile page.
    account(verified_page)
    page=ctx.new_page()
    try:
        for attempt in range(attempts):
            page.goto("https://x.com/lucasyahn",wait_until="domcontentloaded",timeout=45000)
            page.wait_for_timeout(2700)
            target=urlparse(page.url)
            if target.hostname not in ('x.com','www.x.com') or target.path.rstrip('/')!='/lucasyahn':
                raise RuntimeError('X_BROWSER_HUB_TIMELINE_PROFILE_MISMATCH')
            for post in page.locator("article").all()[:25]:
                try:
                    if caption not in post.inner_text(timeout=3000):continue
                    for link in post.locator("a").all():
                        value=link.get_attribute("href") or ""
                        m=re.fullmatch(r"/lucasyahn/status/([0-9]+)/?",value)
                        if not m:continue
                        url="https://x.com/lucasyahn/status/"+m.group(1)
                        page.goto(url,wait_until="domcontentloaded",timeout=45000)
                        page.wait_for_timeout(2300)
                        if caption not in " ".join(page.locator('[data-testid="tweetText"]').all_text_contents()):
                            continue
                        if page.locator("video").count()>0:return url
                except Exception:continue
            if attempt+1<attempts:page.wait_for_timeout(7000)
        return None
    finally:page.close()

def finish(issue,data,post_url):
    number=issue["number"]
    github(f"/issues/{number}/comments","POST",{"body":"X_LOCAL_VIDEO_CONFIRMED_V1\n"+
        json.dumps({"kind":"X_VIDEO_CONFIRMED_V1","account":"lucasyahn","post_url":post_url,
                    "video_verified":True,"idempotency_key":fp(data)})})
    github(f"/issues/{number}","PATCH",{"state":"closed"})
    state(number,"CONFIRMED",post_url=post_url)

def one(issue,data,token):
    n=issue["number"];key=fp(data)
    old=service(token,"/post-status?idempotency_key="+key)
    if old.get("status")=="CONFIRMED":
        url=old.get("post_url") or ""
        if re.fullmatch(r"https://x.com/lucasyahn/status/[0-9]+",url):finish(issue,data,url)
        return
    if old.get("status")!="NOT_FOUND":raise RuntimeError("PREVIOUS_CLOUD_SUBMISSION")
    comments=github(f"/issues/{n}/comments?per_page=100")
    if any(any(tag in str(c.get("body") or "") for tag in (
        "X_SUBMISSION_STARTED_V1","X_POST_SUBMISSION_STARTED_V1",
        "X_SUBMISSION_UNCERTAIN_V1","X_LOCAL_SUBMISSION_STARTED_V1")) for c in comments):
        raise RuntimeError("PREVIOUS_GITHUB_SUBMISSION")
    media=path_for(issue,data)
    media_preflight(media)
    attempts=int(readstate(n).get("attempts") or 0)+1
    state(n,"PREPARING",attempts=attempts)
    _assert_browser_hub_x_profile()
    with sync_playwright() as playwright:
        browser=playwright.chromium.connect_over_cdp("http://127.0.0.1:9224",timeout=18000)
        if len(browser.contexts)!=1:raise RuntimeError("CHROME_CONTEXT_NOT_ISOLATED")
        ctx=browser.contexts[0]
        tabs=[p for p in ctx.pages if p.url.startswith("https://x.com/")]
        if len(tabs)!=1:raise RuntimeError("CHROME_X_TAB_NOT_UNIQUE")
        page=tabs[0]
        _verify_existing_browser_hub_session(page)
        if evidence(ctx,data["caption"],verified_page=page):
            raise RuntimeError("ALREADY_POSTED_RECONCILE")
        dialog=page.locator('[role="dialog"]')
        text_now="\\n".join(dialog.all_inner_texts()) if page.url.endswith("/compose/post") else ""
        resume_ready=(page.url=="https://x.com/compose/post"
                      and data["caption"] in text_now
                      and media.name+": Pronto" in text_now
                      and dialog.locator("video").count()>0)
        if not resume_ready:
            if page.url=="https://x.com/compose/post" and dialog.locator("video").count():
                raise RuntimeError("X_EXISTING_OTHER_MEDIA_DRAFT_REFUSE_TO_OVERWRITE")
            if page.url!="https://x.com/compose/post":
                page.goto("https://x.com/compose/post",wait_until="domcontentloaded",timeout=45000)
            dialog=page.locator('[role="dialog"]')
            writer=dialog.locator('[data-testid="tweetTextarea_0"]').first
            writer.wait_for(state="visible",timeout=25000)
            writer.fill(data["caption"])
            if dialog.locator("video").count():
                raise RuntimeError("X_DRAFT_ALREADY_HAS_MEDIA")
            state(n,"UPLOADING")
            dialog.locator('input[type="file"]').last.set_input_files(str(media),timeout=180000)
        button=dialog.locator('[data-testid="tweetButton"]').first
        end=time.monotonic()+1800
        while time.monotonic()<end:
            account(page)
            text="\n".join(dialog.all_inner_texts())
            if (button.count()==1 and button.is_enabled()
                and dialog.locator("video").count()>0
                and (media.name+": Pronto" in text or media.name+": Ready" in text)):
                break
            if any(s in text.lower() for s in ("vídeo muito longo","video too long","upload failed","falha no carregamento")):
                raise RuntimeError("X_UPLOAD_REJECTED")
            page.wait_for_timeout(5000)
        else:raise RuntimeError("UPLOAD_PROCESSING_TIMEOUT")
        if cloud_owns_queue():raise RuntimeError("CLOUD_PRIMARY_RECOVERED")
        account(page)
        if github(f"/issues/{n}").get("state")!="open":raise RuntimeError("QUEUE_ITEM_ALREADY_CLOSED")
        state(n,"READY")
        service(token,"/claim-local",{"account":"lucasyahn","idempotency_key":key})
        state(n,"SUBMISSION_STARTED",idempotency_key=key)
        # X's compose backdrop can cover the visible/enabled Post button.
        # Playwright's coordinate-based click then hangs until its timeout
        # without dispatching. Directly activate the verified DOM button;
        # this exact path published video #385 (post 2113103163859313089).
        # One irreversible click only, fenced by the PostgreSQL claim.
        button.evaluate("""(element, key) => {
            // Atomic browser-side fence: do not dispatch two POST actions even
            // if another callback invokes this code against the same draft.
            const sent = window.__antharesXSubmissionKeys ||
                         (window.__antharesXSubmissionKeys = new Set());
            if (sent.has(key)) throw new Error("X_DUPLICATE_CLICK_BLOCKED");
            if (!element.isConnected ||
                element.getAttribute("aria-disabled") === "true" ||
                element.disabled) throw new Error("X_POST_BUTTON_NOT_READY");
            sent.add(key);
            element.click();
        }""", key, timeout=12500)
        url=evidence(ctx,data["caption"],attempts=18,verified_page=page)
        if not url:
            state(n,"UNCERTAIN")
            raise RuntimeError("SUBMITTED_BUT_NOT_CONFIRMED")
        service(token,"/confirm-local",{"account":"lucasyahn","idempotency_key":key,
              "post_url":url,"video_verified":True,"caption_verified":True})
        state(n,"CONFIRMED",post_url=url)
        finish(issue,data,url)

def main():
    QUEUE.mkdir(parents=True,exist_ok=True)
    if cloud_owns_queue():return "CLOUD_PRIMARY_ACTIVE"
    token=auth()
    from tools.x_long_schedule import eligible_time
    for issue,data in listed():
        if not eligible_time(data.get("planned_at")):
            continue
        n=issue["number"];prior=readstate(n)
        if prior.get("phase")=="CONFIRMED":
            url=str(prior.get("post_url") or "")
            if re.fullmatch(r"https://x.com/lucasyahn/status/[0-9]+",url):
                try:finish(issue,data,url)
                except Exception:pass
            continue
        if prior.get("phase") in STOP:
            continue
        if int(prior.get("attempts") or 0) >= 3:
            # Only a pre-click preflight failure may be retried periodically.
            # started/uncertain/confirmed remain permanently fenced.
            if prior.get("phase") != "PREFLIGHT_FAILED":
                continue
            try:
                last = datetime.fromisoformat(str(prior["updated"]).replace("Z", "+00:00"))
                if last.tzinfo is None or (datetime.now(TZ) - last).total_seconds() < 5400:
                    continue
            except (ValueError, KeyError, TypeError):
                continue
        try:
            one(issue,data,token)
            return "ONE_ITEM_VISITED"
        except requests.exceptions.HTTPError as exc:
            status=getattr(getattr(exc,"response",None),"status_code",0)
            if status in (404,410):
                old=readstate(n)
                began=old.get("quarantine_started") or datetime.now(timezone.utc).isoformat()
                try:
                    elapsed=(datetime.now(timezone.utc) -
                             datetime.fromisoformat(began.replace("Z","+00:00"))).total_seconds()
                except (ValueError,TypeError):
                    elapsed=0
                if elapsed >= 86400:
                    try:
                        github("/issues/"+str(n)+"/comments","POST",{"body":
                            "X_MEDIA_DISCARDED_AFTER_24H media_http="+str(status)+
                            " first_seen="+began})
                        github("/issues/"+str(n),"PATCH",{"state":"closed"})
                        state(n,"DISCARDED",quarantine_started=began,media_http=status)
                    except Exception:
                        state(n,"QUARANTINED_MEDIA",quarantine_started=began,media_http=status)
                    continue
                state(n,"QUARANTINED_MEDIA",quarantine_started=began,media_http=status)
                if old.get("phase")!="QUARANTINED_MEDIA":
                    try:github("/issues/380/comments","POST",{"body":
                        "X_LOCAL_P0_MEDIA_QUARANTINE issue="+str(n)+
                        " media_http="+str(status)+" deadline_24h="+began})
                    except Exception:pass
                # Crucial: 404 must not consume a publication slot or hold
                # another healthy issue until the next 10-minute scheduler run.
                continue
            state(n,"PREFLIGHT_FAILED",error_type=type(exc).__name__,error_code="MEDIA_HTTP_"+str(status) if status else "HTTP_PREFLIGHT_FAILED")
            continue
        except Exception as exc:
            # Log only a fixed-shape diagnostic code; never disclose browser
            # tokens, URLs or exception payloads from external services.
            msg=str(exc)
            safe_code=msg if re.fullmatch(r"[A-Z][A-Z0-9_]{2,100}", msg) else type(exc).__name__
            phase=readstate(n).get("phase")
            if phase=="SUBMISSION_STARTED":
                state(n,"UNCERTAIN",error_type=type(exc).__name__)
            elif phase not in STOP:
                state(n,"PREFLIGHT_FAILED",error_type=type(exc).__name__,error_code=safe_code)
            try:github("/issues/380/comments","POST",{"body":
                "X_LOCAL_P0 issue="+str(n)+" error="+type(exc).__name__})
            except Exception:pass
            if phase=="SUBMISSION_STARTED":
                return "UNCERTAIN_FENCED_NEXT_SCHEDULE"
            # Preflight failed safely before a POST; try the next distinct issue.
            continue
    return "QUEUE_EMPTY_OR_FENCED"

if __name__=="__main__":
    try:print("X_LOCAL_RESULT="+main(),flush=True)
    except Exception as exc:print("X_LOCAL_FATAL="+type(exc).__name__,flush=True)
