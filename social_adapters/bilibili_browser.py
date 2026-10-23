#!/usr/bin/env python3
"""Bilibili creator-studio browser publisher. No official posting API.

A successful click is NOT evidence of a public upload. Only a newly observed
video on the expected creator profile may confirm a publication.
"""
import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import urlsplit, urljoin

class AuthenticationRequired(RuntimeError): pass
class IdentityMismatch(RuntimeError): pass
class PublicationUnverified(RuntimeError): pass
class BrowserPublishError(RuntimeError): pass

def normalize_account(value):
    return str(value or "").strip().lstrip("@").casefold()

def canonical_video_url(href):
    if not href:
        return ""
    if href.startswith("/"):
        href = urljoin("https://www.bilibili.com", href)
    u = urlsplit(href)
    if u.scheme != "https" or (u.hostname or "").lower() not in {"www.bilibili.com","bilibili.com"}:
        return ""
    match = re.fullmatch(r"/video/(BV[0-9A-Za-z]+)(?:/)?", u.path)
    return f"https://www.bilibili.com/video/{match.group(1)}" if match else ""

def external_id_from_url(url):
    normalized = canonical_video_url(url)
    return normalized.rsplit("/", 1)[-1] if normalized else ""

def canonical_space_url(account):
    account = normalize_account(account)
    if not re.fullmatch(r"[0-9]+", account):
        raise ValueError("Bilibili account must be the numeric creator UID")
    return f"https://space.bilibili.com/{account}/video"

def file_sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda: f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def _latest_video(page):
    links=page.locator('a[href*="/video/BV"]')
    for i in range(min(links.count(),40)):
        url=canonical_video_url(links.nth(i).get_attribute("href") or "")
        if url: return url
    return ""

def _login_wall(page):
    return any(token in page.url.lower() for token in ("/login","passport.bilibili.com"))

def _verify_creator(page, account):
    page.goto("https://member.bilibili.com/platform/home",wait_until="domcontentloaded",timeout=45000)
    if _login_wall(page): raise AuthenticationRequired("Bilibili creator login required")
    # The creator UID must be verified from the authenticated creator studio,
    # never inferred from the public profile page.
    marker=page.locator(f'a[href*="space.bilibili.com/{account}"], a[href*="/{account}/"]').first
    try:
        marker.wait_for(state="attached",timeout=5000)
    except Exception as exc:
        raise IdentityMismatch("Expected creator UID not verified in signed-in studio") from exc

def _submit(page,video,title,description):
    page.goto("https://member.bilibili.com/platform/upload/video/frame",wait_until="domcontentloaded",timeout=45000)
    if _login_wall(page): raise AuthenticationRequired("Creator upload login required")
    inp=page.locator('input[type="file"]').first
    try: inp.wait_for(state="attached",timeout=12000)
    except Exception as exc: raise BrowserPublishError("Video file input not found") from exc
    inp.set_input_files(str(video))
    title_box=page.locator('input[placeholder*="标题"], input[placeholder*="title"], input[name="title"]').first
    try:
        title_box.wait_for(state="visible",timeout=30000)
        title_box.fill(title[:80])
    except Exception as exc: raise BrowserPublishError("Title input not found") from exc
    if description:
        editor=page.locator('textarea, [contenteditable="true"]').first
        try: editor.fill(description[:2000])
        except Exception: pass
    # Do not blindly accept copyright, category, licensing or other declarations.
    # If additional required controls are present, the upload remains unsubmitted.
    submit=page.get_by_role("button",name=re.compile(r"^(立即投稿|发布|提交|Publish|Submit)$",re.I)).first
    try: submit.wait_for(state="visible",timeout=15000)
    except Exception as exc: raise BrowserPublishError("Submit control not found; manual metadata may be required") from exc
    if not submit.is_enabled(): raise BrowserPublishError("Submit disabled; required metadata or upload pending")
    submit.click(timeout=5000)

def publish(platform,video,caption,account,profile,title="",commit=False,headless=True):
    if platform.casefold()!="bilibili": raise ValueError("unsupported platform")
    uid=normalize_account(account)
    space=canonical_space_url(uid)
    path=Path(video).resolve()
    if not path.is_file(): raise FileNotFoundError(path)
    result={"platform":"bilibili","account":uid,"video":str(path),"content_sha256":file_sha256(path),"title":(title or caption or "Anthares")[:80]}
    if not commit: return {**result,"status":"DRY_RUN"}
    from playwright.sync_api import sync_playwright
    pdir=Path(profile).resolve();pdir.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        ctx=p.chromium.launch_persistent_context(str(pdir),headless=headless,viewport={"width":1440,"height":900})
        page=ctx.pages[0] if ctx.pages else ctx.new_page()
        submitted=False
        try:
            _verify_creator(page,uid)
            page.goto(space,wait_until="domcontentloaded",timeout=45000)
            previous=_latest_video(page)
            _submit(page,path,result["title"],caption)
            submitted=True
            deadline=time.monotonic()+120
            while time.monotonic()<deadline:
                page.goto(space,wait_until="domcontentloaded",timeout=45000)
                current=_latest_video(page)
                if current and current!=previous:
                    rid=external_id_from_url(current)
                    if rid:
                        return {**result,"status":"CONFIRMED","remote_id":rid,"confirmation_evidence":{"permalink":current,"previous_latest":previous}}
                page.wait_for_timeout(3000)
            return {**result,"status":"UNCERTAIN","reason":"No new public video observed after submit"}
        except (AuthenticationRequired,IdentityMismatch) as exc:
            return {**result,"status":"UNCERTAIN" if submitted else ("AUTH_REQUIRED" if isinstance(exc,AuthenticationRequired) else "IDENTITY_MISMATCH"),"reason":str(exc)}
        except Exception as exc:
            return {**result,"status":"UNCERTAIN" if submitted else "FAILED","reason":str(exc)}
        finally: ctx.close()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--platform",default="bilibili",choices=["bilibili"])
    p.add_argument("--account",required=True,help="Numeric Bilibili creator UID")
    p.add_argument("--video",required=True)
    p.add_argument("--caption",default="")
    p.add_argument("--title",default="")
    p.add_argument("--profile",required=True)
    p.add_argument("--commit",action="store_true")
    p.add_argument("--headed",action="store_true")
    a=p.parse_args()
    print(json.dumps(publish(a.platform,a.video,a.caption,a.account,a.profile,title=a.title,commit=a.commit,headless=not a.headed),ensure_ascii=False,sort_keys=True))

if __name__=="__main__": main()
