#!/usr/bin/env python3
"""Read-only, authenticated TikTok Studio audit of the 10 Oct 27 uncertain clips.

All evidence is bound to an exact per-segment marker AND a video ID in the
same Studio record. Never uploads, claims a lease, changes statuses, or clicks
Publish. A missing match remains UNVERIFIED, never inferred unpublished.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
sys.path.insert(0,str(ROOT/"direct-tiktok-publisher"))
from cortes_tiktok_queue_consumer import marker
from cortes_tiktok_hosted_publish import preflight_vault
from playwright.sync_api import sync_playwright

ACCOUNT="universo.anthares"
SEGMENTS=(
    "g1:A7BsgCe3-oo:3463:3503",
    "g1:A7BsgCe3-oo:3503:3544",
    "g1:A7BsgCe3-oo:2513:2554",
    "g1:A7BsgCe3-oo:4741:4781",
    "g1:A7BsgCe3-oo:4781:4822",
    "g1:A7BsgCe3-oo:4822:4864",
    "g1:A7BsgCe3-oo:4864:4905",
    "g1:A7BsgCe3-oo:4905:4946",
    "g1:A7BsgCe3-oo:4946:4989",
    "g1:A7BsgCe3-oo:4989:5029",
)
MARKERS={s:marker(s) for s in SEGMENTS}
VID=re.compile(r"^[0-9]{12,25}$")
URL=re.compile(r"/@"+re.escape(ACCOUNT)+r"/video/([0-9]{12,25})")

def inspect_state(node, hits, depth=0):
    if depth>22:
        return
    if isinstance(node,dict):
        video=str(node.get("id") or node.get("aweme_id") or "")
        caption=str(node.get("desc") or node.get("description") or node.get("title") or "").casefold()
        owner=str(node.get("uniqueId") or node.get("unique_id") or "").casefold().lstrip("@")
        # The record is a TikTok Studio record from an authenticated owner session.
        # Refuse contradictory explicit owner identity if present in the record.
        if VID.fullmatch(video) and (not owner or owner==ACCOUNT):
            for segment,mark in MARKERS.items():
                if mark in caption:
                    hits[segment].add(video)
        for value in node.values():
            if isinstance(value,(dict,list)):
                inspect_state(value,hits,depth+1)
    elif isinstance(node,list):
        for value in node[:700]:
            inspect_state(value,hits,depth+1)

def inspect_page(page,hits):
    for selector in ("#__UNIVERSAL_DATA_FOR_REHYDRATION__","#__SIGI_STATE"):
        try:
            raw=page.locator(selector).text_content(timeout=1300)
            if raw:
                inspect_state(json.loads(raw),hits)
        except (ValueError,Exception):
            pass
    # Scope each candidate to its own card/row. Broad body text is never proof.
    rows=page.locator('a[href*="/video/"]').evaluate_all("""xs=>xs.map(a=>{
      const card=a.closest('tr,[role="row"],[data-e2e*="video-card"],li');
      return {url:a.href, caption:(card?card.innerText:(a.innerText||a.getAttribute('aria-label')||'')).slice(0,1600)}
    })""")
    for row in rows[:600]:
        m=URL.search(str(row.get("url") or ""))
        if not m:
            continue
        caption=str(row.get("caption") or "").casefold()
        for segment,mark in MARKERS.items():
            if mark in caption:
                hits[segment].add(m.group(1))
    return len(rows)

def next_page(page):
    # TikTok Studio may use either pagination or an inner scroll container.
    # Only navigate the owned post list; never select per-video action menus.
    for selector in (
        'button[aria-label="Next page"]',
        'button[aria-label="Next"]',
        'button[aria-label="Próxima página"]',
        'button[title="Next page"]',
        '[data-e2e="pagination-next"]',
        '[data-e2e="next-page"]',
        '.ant-pagination-next:not(.ant-pagination-disabled) button',
    ):
        button=page.locator(selector).first
        try:
            if button.count() and button.is_visible(timeout=350) and button.is_enabled():
                button.click(timeout=3000)
                page.wait_for_timeout(1200)
                return True
        except Exception:
            continue
    for label in (r"^(Next|Próxima página|Próximo|Load more|Carregar mais)$",):
        try:
            button=page.get_by_role("button",name=re.compile(label,re.I)).first
            if button.count() and button.is_visible(timeout=350) and button.is_enabled():
                button.click(timeout=3000)
                page.wait_for_timeout(1200)
                return True
        except Exception:
            pass
    try:
        page.evaluate("""() => {
          const all=[document.scrollingElement,...document.querySelectorAll('main,section,div,ul')];
          for(const e of all){
            if(!e || e.scrollHeight<e.clientHeight+100 || e.clientHeight<110)continue;
            const y=getComputedStyle(e).overflowY;
            if(/auto|scroll|overlay/.test(y) || e===document.scrollingElement){
              e.scrollTop=e.scrollHeight;
            }
          }
          window.scrollTo(0,document.body.scrollHeight);
        }""")
        page.mouse.wheel(0,1800)
        page.wait_for_timeout(1400)
    except Exception:
        pass
    return False

def history_controls(page):
    try:
        return page.evaluate("""() => ({
          nav: [...document.querySelectorAll('button,[role=button],input,select')]
            .map(x=>({role:x.tagName.toLowerCase(),text:(
              x.getAttribute('aria-label')||x.getAttribute('title')||
              x.getAttribute('placeholder')||x.innerText||'').trim().slice(0,55)}))
            .filter(x=>/next|prev|older|page|página|próxi|carregar|filter|filtro|buscar|search|date|data|post|publicaç|gerenciar/i.test(x.text))
            .slice(0,45),
          scroll_regions: [...document.querySelectorAll('main,section,div')]
            .filter(e=>e.scrollHeight>e.clientHeight+100 && e.clientHeight>110 &&
              /auto|scroll|overlay/.test(getComputedStyle(e).overflowY))
            .map(e=>({tag:e.tagName.toLowerCase(),height:e.clientHeight,
              scroll_height:e.scrollHeight})).slice(0,12)
        })""")
    except Exception:
        return {"nav":[],"scroll_regions":[]}


def main():
    state=preflight_vault()  # exact logged-in @universo.anthares identity
    hits={s:set() for s in SEGMENTS}
    pages=0
    stagnant=0
    distinct_urls=set()
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage","--disable-gpu"])
        try:
            ctx=browser.new_context(storage_state=state,locale="pt-BR",viewport={"width":1440,"height":1000})
            page=ctx.new_page()
            try:
                r=page.goto("https://www.tiktok.com/tiktokstudio/content",wait_until="domcontentloaded",timeout=45000)
                page.wait_for_timeout(4500)
                if not page.url.startswith("https://www.tiktok.com/tiktokstudio/content") or (r and r.status>=400):
                    raise RuntimeError("TIKTOK_STUDIO_CONTENT_UNAVAILABLE")
                if page.locator('input[type="password"]').count() or "/login" in page.url:
                    raise RuntimeError("TIKTOK_STUDIO_SESSION_INVALID")
                controls=history_controls(page)
                for _ in range(90):
                    before=sum(len(v) for v in hits.values())
                    count=inspect_page(page,hits)
                    pages+=1
                    urls=page.locator('a[href*="/video/"]').evaluate_all("es=>es.map(a=>a.href)")
                    fingerprint=tuple(urls[:25])
                    is_new=fingerprint not in distinct_urls
                    distinct_urls.add(fingerprint)
                    if all(len(v)==1 for v in hits.values()):
                        break
                    advanced=next_page(page)
                    stagnant=0 if advanced or is_new or sum(len(v) for v in hits.values())>before else stagnant+1
                    if stagnant>=4 or count==0 and pages>=5:
                        break
            finally:
                ctx.close()
        finally:
            browser.close()
    report={
        "account":ACCOUNT,"authenticated_owner":True,"pages_scanned":pages,
        "unique_page_fingerprints":len(distinct_urls),
        "history_controls":controls,
        "items":[{"segment_id":s,"status":"EXACT_MATCH" if len(hits[s])==1 else
                  "AMBIGUOUS" if len(hits[s])>1 else "UNVERIFIED",
                  "remote_id":next(iter(hits[s])) if len(hits[s])==1 else None}
                 for s in SEGMENTS],
    }
    print("CORTES_TIKTOK_UNCERTAIN_BATCH_AUDIT="+json.dumps(report,sort_keys=True,separators=(",",":")),flush=True)
    print("CORTES_TIKTOK_UNCERTAIN_BATCH_EXACT="+str(sum(x["status"]=="EXACT_MATCH" for x in report["items"])),flush=True)
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as exc:
        print("CORTES_TIKTOK_UNCERTAIN_BATCH_ERROR="+type(exc).__name__,flush=True)
        raise
