#!/usr/bin/env python3
"""Owned TikTok Studio posted-video inventory, with public-profile fallback.

Read-only. Retrieve video IDs and descriptions from the authenticated Studio
content page, pairing each ID only with the description in its own record.
Never interpret an unrelated number on the page as a publication.
"""
from __future__ import annotations

import json
import re
import time

ACCOUNT="universo.anthares"
ID_RE=re.compile(r"^[0-9]{12,25}$")


def collect_posts(node, depth=0, found=None):
    found=found if found is not None else {}
    if depth>22:
        return found
    if isinstance(node,dict):
        vid=str(node.get("id") or node.get("aweme_id") or "")
        caption=str(node.get("desc") or node.get("description") or node.get("title") or "")
        if ID_RE.fullmatch(vid) and caption:
            previous=found.get(vid)
            if not previous or len(caption)>len(previous.get("text","")):
                found[vid]={"id":vid,"url":f"https://www.tiktok.com/@{ACCOUNT}/video/{vid}",
                            "text":" ".join(caption.split())[:900]}
        for child in node.values():
            if isinstance(child,(dict,list)):
                collect_posts(child,depth+1,found)
    elif isinstance(node,list):
        for child in node[:500]:
            collect_posts(child,depth+1,found)
    return found


def inventory_studio(account=ACCOUNT, state=None):
    from playwright.sync_api import sync_playwright
    if str(account).strip().lstrip("@").casefold()!=ACCOUNT:
        raise RuntimeError("TIKTOK_STUDIO_ACCOUNT_MISMATCH")
    if state is None:
        from tiktok_session_authority import load_canonical_state
        state,_=load_canonical_state()
    found={}
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=[
            "--no-sandbox","--disable-dev-shm-usage","--disable-gpu"])
        try:
            ctx=browser.new_context(storage_state=state,locale="pt-BR",
                                    viewport={"width":1440,"height":900})
            page=ctx.new_page()
            response=page.goto("https://www.tiktok.com/tiktokstudio/content",
                               wait_until="domcontentloaded",timeout=45000)
            page.wait_for_timeout(7000)
            if not page.url.startswith("https://www.tiktok.com/"):
                raise RuntimeError("TIKTOK_STUDIO_WRONG_DOMAIN")
            if "/login" in page.url or page.locator('input[type="password"]').count():
                raise RuntimeError("TIKTOK_STUDIO_LOGIN_REQUIRED")
            if response and response.status>=400:
                raise RuntimeError("TIKTOK_STUDIO_HTTP_ERROR")
            for selector in ("#__UNIVERSAL_DATA_FOR_REHYDRATION__","#__SIGI_STATE"):
                try:
                    raw=page.locator(selector).text_content(timeout=2200)
                    collect_posts(json.loads(raw or "{}"),found=found)
                except (ValueError,Exception):
                    pass
            # Associate an anchor with a caption only if its own label or
            # immediately enclosing card contains the caption; never scan
            # unrelated page text for video IDs.
            links=page.locator('a[href*="/video/"]').evaluate_all(
                "(xs)=>xs.map(a=>({href:a.href,text:(a.closest('article')?.innerText||a.closest('[data-e2e]')?.innerText||a.innerText||'').slice(0,900)}))"
            )
            for link in links:
                match=re.search(r"/video/(\d{12,25})(?:[/?#]|$)",str(link.get("href") or ""))
                label=" ".join(str(link.get("text") or "").split())
                if match and label:
                    vid=match.group(1)
                    if vid not in found or len(label)>len(found[vid]["text"]):
                        found[vid]={"id":vid,"url":f"https://www.tiktok.com/@{ACCOUNT}/video/{vid}",
                                    "text":label[:900]}
        finally:
            browser.close()
    print("TIKTOK_STUDIO_POST_INVENTORY_COUNT="+str(len(found)),flush=True)
    return list(found.values())


def inventory_all_videos(account=ACCOUNT):
    results=inventory_studio(account)
    if results:
        return results
    import tiktok_worker as tw
    return tw.inventory_profile_videos(account)


if __name__=="__main__":
    try:
        rows=inventory_all_videos()
        print("TIKTOK_STUDIO_INVENTORY_VERIFIED_COUNT="+str(len(rows)),flush=True)
    except Exception as exc:
        print("TIKTOK_STUDIO_INVENTORY_ERROR="+type(exc).__name__,flush=True)
        raise
