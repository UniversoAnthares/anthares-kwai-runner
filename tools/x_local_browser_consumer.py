"""Hidden, serialized Windows X publication fallback. Run as interactive Lucas via pythonw.
One queued long video per invocation; Northflank cloud remains primary.
"""
import hashlib, json, os, re, subprocess, time
from datetime import datetime
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
STOP={"SUBMISSION_STARTED","UNCERTAIN","CONFIRMED"}

def github(path, method="GET", body=None):
    cmd=["gh","api","repos/"+REPO+path]
    if method!="GET":cmd+=["-X",method,"--input","-"]
    result=subprocess.run(cmd,input=json.dumps(body) if body is not None else None,
                          capture_output=True,text=True,timeout=35)
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
    key=os.getenv("NORTHFLANK_API_TOKEN")
    if not key:raise RuntimeError("NORTHFLANK_TOKEN_UNAVAILABLE")
    response=requests.get("https://api.northflank.com/v1/projects/default/services/anthares-ara-northflank/runtime-environment",
                          headers={"Authorization":"Bearer "+key},timeout=20)
    response.raise_for_status()
    token=response.json()["data"]["runtimeEnvironment"]["ARA_SHARED"]
    if not token:raise RuntimeError("ARA_SHARED_UNAVAILABLE")
    return token

def service(token,path,body=None):
    try:
        r=requests.request("POST" if body is not None else "GET",BASE+path,
          json=body,headers={"Authorization":"Bearer "+token},timeout=35)
    except requests.RequestException:raise RuntimeError("CLOUD_LEDGER_UNREACHABLE") from None
    if r.status_code==409:raise RuntimeError("POST_ALREADY_CLAIMED")
    if r.status_code==429:raise RuntimeError("DAILY_MAX_10")
    if r.status_code!=200:raise RuntimeError("CLOUD_LEDGER_HTTP_"+str(r.status_code))
    data=r.json()
    if not data.get("ok"):raise RuntimeError("CLOUD_LEDGER_NEGATIVE")
    return data

def cloud_owns_queue():
    # A healthy browser alone is not an armed queue consumer. Do not let it
    # starve local standby when the GitHub cloud publisher is disarmed.
    try:
        settings=github("/actions/variables/ANTHARES_X_AUTOPUBLISH")
        if str(settings.get("value") or "").lower() not in ("1","true"):return False
        r=requests.get(BASE+"/health",timeout=8)
        j=r.json()
        return r.status_code==200 and j.get("browser_ready") is True and j.get("vault_ready") is True
    except Exception:return False

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
    tab=page.locator('[data-testid="SideNav_AccountSwitcher_Button"]')
    if tab.count()!=1:raise RuntimeError("ACCOUNT_UNCONFIRMED")
    names=re.findall(r"(?<![A-Za-z0-9_])@([A-Za-z0-9_]{1,15})(?![A-Za-z0-9_])",
                     tab.first.inner_text(timeout=9000))
    if names!=["lucasyahn"]:raise RuntimeError("WRONG_X_ACCOUNT")

def evidence(ctx,caption,attempts=1):
    page=ctx.new_page()
    try:
        for attempt in range(attempts):
            page.goto("https://x.com/lucasyahn",wait_until="domcontentloaded",timeout=45000)
            page.wait_for_timeout(2700);account(page)
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
    with sync_playwright() as playwright:
        browser=playwright.chromium.connect_over_cdp("http://127.0.0.1:9224",timeout=18000)
        if len(browser.contexts)!=1:raise RuntimeError("CHROME_CONTEXT_NOT_ISOLATED")
        ctx=browser.contexts[0]
        tabs=[p for p in ctx.pages if p.url.startswith("https://x.com/")]
        if len(tabs)!=1:raise RuntimeError("CHROME_X_TAB_NOT_UNIQUE")
        page=tabs[0];account(page)
        if evidence(ctx,data["caption"]):
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
        button.click(timeout=55000)
        url=evidence(ctx,data["caption"],attempts=18)
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
    for issue,data in listed():
        n=issue["number"];prior=readstate(n)
        if prior.get("phase")=="CONFIRMED":
            url=str(prior.get("post_url") or "")
            if re.fullmatch(r"https://x.com/lucasyahn/status/[0-9]+",url):
                try:finish(issue,data,url)
                except Exception:pass
            continue
        if prior.get("phase") in STOP or int(prior.get("attempts") or 0)>=3:continue
        try:one(issue,data,token)
        except Exception as e:
            phase=readstate(n).get("phase")
            if phase=="SUBMISSION_STARTED":state(n,"UNCERTAIN",error_type=type(e).__name__)
            elif phase not in STOP:state(n,"PREFLIGHT_FAILED",error_type=type(e).__name__)
            try:github("/issues/380/comments","POST",{"body":"X_LOCAL_P0 issue="+str(n)+" error="+type(e).__name__})
            except Exception:pass
        return "ONE_ITEM_VISITED"
    return "QUEUE_EMPTY_OR_FENCED"

if __name__=="__main__":
    try:print("X_LOCAL_RESULT="+main(),flush=True)
    except Exception as exc:print("X_LOCAL_FATAL="+type(exc).__name__,flush=True)
