#!/usr/bin/env python3
"""Read-only Studio evidence for two pre-cutover uncertain segments."""
import json,sys,time
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
from cortes_tiktok_lucasrosalem4_cloud_publish import state_from_secret,studio,marker,ACCOUNT
SEGMENTS=("g1:fOmihuHUT1M:1693:1727","g1:fOmihuHUT1M:1727:1763")
def main():
    state=state_from_secret()
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage","--disable-gpu"])
        try:
            ctx=browser.new_context(storage_state=state,locale="pt-BR")
            try:
                page=ctx.new_page()
                try:
                    records=studio(page)
                finally:page.close()
            finally:ctx.close()
        finally:browser.close()
    evidence={"observed_at":datetime.now(timezone.utc).isoformat(),"account":ACCOUNT,
              "method":"read_only_authenticated_studio_inventory_first_100_links",
              "inventory_count":len(records),"inventory_complete":False,
              "results":[]}
    for segment in SEGMENTS:
        key=marker(segment).lower()
        exact=[id for id,title in records.items() if key in title.lower()]
        evidence["results"].append({"segment_id":segment,"marker":key,
             "exact_match_count":len(exact),
             "remote_urls":["https://www.tiktok.com/@"+ACCOUNT+"/video/"+id for id in exact],
             "determination":"confirmed_candidate" if len(exact)==1 else
                 ("ambiguous" if len(exact)>1 else "not_found_in_partial_inventory")})
    print("TIKTOK_UNCERTAIN_READ_ONLY_EVIDENCE="+json.dumps(evidence,sort_keys=True),flush=True)
    if any(x["exact_match_count"]>1 for x in evidence["results"]):return 2
    return 0
if __name__=="__main__":sys.exit(main())
