#!/usr/bin/env python3
"""Read-only forensic check for an uncertain TikTok publication. No queue writes."""
from __future__ import annotations
import json, os, re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"direct-tiktok-publisher"))
sys.path.insert(0,str(ROOT/"tools"))
from tiktok_session_authority import load_canonical_state
from cortes_tiktok_queue_consumer import marker

TARGET=os.getenv("CORTES_TIKTOK_FORENSIC_SEGMENT_ID","")
ACCOUNT="universo.anthares"
VIDEO_RE=re.compile(r"^[0-9]{12,25}$")

def extract_ids(node, mark, depth=0):
    if depth>18:return set()
    found=set()
    if isinstance(node,dict):
        title=str(node.get("desc") or node.get("description") or node.get("title") or "").casefold()
        remote=str(node.get("id") or node.get("aweme_id") or "")
        if mark in title and VIDEO_RE.fullmatch(remote):
            found.add(remote)
        for value in node.values():
            if isinstance(value,(dict,list)):
                found.update(extract_ids(value,mark,depth+1))
    elif isinstance(node,list):
        for item in node[:400]:
            found.update(extract_ids(item,mark,depth+1))
    return found

def main():
    if not TARGET.startswith("g1:") or TARGET.count(":")!=3:
        print("TIKTOK_FORENSIC=SEGMENT_UNSET",flush=True)
        return 2
    mark=marker(TARGET)
    state,_=load_canonical_state()
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage","--disable-gpu"])
        try:
            ctx=browser.new_context(storage_state=state,locale="pt-BR",viewport={"width":1440,"height":900})
            page=ctx.new_page()
            for kind,url in (
                ("creator_content","https://www.tiktok.com/tiktokstudio/content"),
                ("public_profile",f"https://www.tiktok.com/@{ACCOUNT}")):
                try:
                    response=page.goto(url,wait_until="domcontentloaded",timeout=40000)
                    page.wait_for_timeout(6500)
                    body=(page.locator("body").inner_text(timeout=2800) or "").casefold()
                    ids=set()
                    for selector in ("#__UNIVERSAL_DATA_FOR_REHYDRATION__","#__SIGI_STATE"):
                        try:
                            raw=page.locator(selector).text_content(timeout=1600) or "{}"
                            ids.update(extract_ids(json.loads(raw),mark))
                        except (ValueError,Exception):
                            pass
                    links=page.locator('a[href*="/video/"]').evaluate_all(
                        "(els)=>els.map(x=>({url:x.href,text:(x.innerText||x.getAttribute('aria-label')||'').slice(0,700)}))"
                    )
                    for l in links:
                        m=re.search(r"/video/(\d{12,25})",str(l.get("url") or ""))
                        if m and mark in str(l.get("text") or "").casefold():
                            ids.add(m.group(1))
                    results.append({
                        "surface":kind,
                        "http_ok":bool(response and 200<=response.status<400),
                        "logged_out":"/login" in page.url or bool(page.locator('input[type=password]').count()),
                        "marker_in_visible_text":mark in body,
                        "matched_remote_ids":sorted(ids),
                        "video_link_count":min(len(links),300),
                    })
                except Exception as e:
                    results.append({"surface":kind,"error_type":type(e).__name__})
        finally:
            browser.close()
    print("CORTES_TIKTOK_POST_READONLY_AUDIT="+json.dumps(results,separators=(",",":"),sort_keys=True),flush=True)
    return 0

if __name__=="__main__":
    try:sys.exit(main())
    except Exception as e:
        print("TIKTOK_FORENSIC_ERROR="+type(e).__name__,flush=True)
        sys.exit(2)
