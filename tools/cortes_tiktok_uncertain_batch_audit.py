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
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
sys.path.insert(0,str(ROOT/"direct-tiktok-publisher"))
from cortes_tiktok_queue_consumer import marker, oidc, qcall
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
TITLES={
    "g1:A7BsgCe3-oo:3463:3503": "Rumores sobre a batalha do estabulo e o tiro",
    "g1:A7BsgCe3-oo:3503:3544": "O tiro no ombro e a mentira do espetaculo",
    "g1:A7BsgCe3-oo:2513:2554": "A estrutura de fábula e a imanência em Animal Farm",
    "g1:A7BsgCe3-oo:4741:4781": "Resgatando os nomes dos personagens e equinos na trama",
    "g1:A7BsgCe3-oo:4781:4822": "A fuga da égua Mimosa e o apego aos velhos hábitos na fazenda",
    "g1:A7BsgCe3-oo:4822:4864": "A personagem Quitéria e a leitura das letras do alfabeto",
    "g1:A7BsgCe3-oo:4864:4905": "O terceiro regime e os Porquinhos diante de Napoleão",
    "g1:A7BsgCe3-oo:4905:4946": "Confessar crimes que não cometeram na União Soviética",
    "g1:A7BsgCe3-oo:4946:4989": "Os cães e os inimigos do regime na fazenda",
    "g1:A7BsgCe3-oo:4989:5029": "Moinho em construção e a aurora no horizonte verdejante",
}

OCT27_START=int(datetime(2026,10,27,tzinfo=timezone.utc).timestamp())
OCT29_END=int(datetime(2026,10,30,tzinfo=timezone.utc).timestamp())

def norm(text):
    text=unicodedata.normalize("NFKD",str(text).casefold())
    text="".join(c for c in text if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+",text))

# Full caption may be truncated by the publisher, so require its long,
# uniquely distinguishing prefix. Short search input is only discovery.
PREFIXES={s:norm(title)[:47].rsplit(" ",1)[0] for s,title in TITLES.items()}

def inspect_title_candidates(page,candidates):
    # Independent of #anthares marker: title + exact owner video URL +
    # independently decoded TikTok video-ID date, all in the SAME card.
    # Candidate ≠ confirmation; only the exact stable marker can auto-confirm.
    rows=page.locator('a[href*="/video/"]').evaluate_all("""xs=>xs.map(a=>{
      const card=a.closest('tr,[role="row"],[data-e2e*="video-card"],li');
      return {url:a.href,caption:(card?card.innerText:(a.innerText||a.getAttribute('aria-label')||'')).slice(0,1600)}
    })""")
    for row in rows[:600]:
        m=URL.search(str(row.get("url") or ""))
        if not m:
            continue
        remote=m.group(1)
        # TikTok's high-order video ID component encodes creation time.
        stamp=int(remote)>>32
        if not OCT27_START-86400<=stamp<=OCT29_END:
            continue
        caption=norm(row.get("caption") or "")
        for segment,prefix in PREFIXES.items():
            if prefix in caption:
                candidates[segment].add(remote)
    return len(rows)

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
    # Evidence for the October 27 incidents remains in the immutable Neon audit.
    # Skip an expensive authenticated 20-query Studio scan after all historical
    # uncertain rows have been administratively closed without retransmission.
    current=qcall("status",oidc())
    if current.get("ok") is not True:
        raise RuntimeError("TIKTOK_HISTORIC_LEDGER_STATUS_UNAVAILABLE")
    if int((current.get("count") or {}).get("uncertain",0))==0:
        print("CORTES_TIKTOK_HISTORIC_UNCERTAIN_TERMINALLY_CLOSED_NO_REUPLOAD=1",flush=True)
        return 0
    state=preflight_vault()  # exact logged-in @universo.anthares identity
    hits={s:set() for s in SEGMENTS}
    candidates={s:set() for s in SEGMENTS}
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
                search=page.get_by_placeholder(re.compile(r"Pesquise a descri|Search.*description",re.I)).first
                search_used=bool(search.count())
                search_links={}
                if search_used:
                    # Search by each unique marker through the official signed-in
                    # Studio description filter. Enter/clear are read-only UI actions.
                    for segment,mark in MARKERS.items():
                        search.fill(mark,timeout=3000)
                        search.press("Enter",timeout=3000)
                        page.wait_for_timeout(2100)
                        if "/login" in page.url or page.locator('input[type="password"]').count():
                            raise RuntimeError("TIKTOK_STUDIO_SEARCH_SESSION_LOST")
                        search_links[segment]=inspect_page(page,hits)
                    # Second forensic route: search the actual editorial
                    # title rather than the marker, which the failed Oct27
                    # post may never have written to the remote caption.
                    for segment,title in TITLES.items():
                        search.fill(" ".join(title.split()[:5]),timeout=3000)
                        search.press("Enter",timeout=3000)
                        page.wait_for_timeout(1500)
                        if "/login" in page.url or page.locator('input[type="password"]').count():
                            raise RuntimeError("TIKTOK_STUDIO_TITLE_SEARCH_SESSION_LOST")
                        inspect_title_candidates(page,candidates)
                    search.fill("",timeout=3000)
                    page.wait_for_timeout(450)
                    pages=2*len(MARKERS)
                else:
                    for _ in range(90):
                        before=sum(len(v) for v in hits.values())
                        count=inspect_page(page,hits)
                        inspect_title_candidates(page,candidates)
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
                # A separate read-only surface, not the Studio search index.
                # The owner link remains mandatory for any candidate.
                try:
                    response=page.goto("https://www.tiktok.com/@"+ACCOUNT,wait_until="domcontentloaded",timeout=35000)
                    page.wait_for_timeout(2400)
                    if (response is not None and response.status<400 and
                        "/login" not in page.url and
                        not page.locator('input[type="password"]').count()):
                        inspect_page(page,hits)
                        inspect_title_candidates(page,candidates)
                        public_profile_scanned=True
                    else:
                        public_profile_scanned=False
                except Exception:
                    public_profile_scanned=False
            finally:
                ctx.close()
        finally:
            browser.close()
    report={
        "account":ACCOUNT,"authenticated_owner":True,"pages_scanned":pages,
        "unique_page_fingerprints":len(distinct_urls),
        "history_controls":controls,
        "description_search_used":search_used,
        "search_video_links_per_query":search_links,
        "title_time_candidates_per_segment":{s:sorted(candidates[s]) for s in SEGMENTS},
        "public_profile_scanned":public_profile_scanned,
        "items":[{"segment_id":s,"status":"EXACT_MATCH" if len(hits[s])==1 else
                  "AMBIGUOUS" if len(hits[s])>1 else
                  "TITLE_TIME_CANDIDATE_NEEDS_REVIEW" if candidates[s] else "UNVERIFIED",
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
