#!/usr/bin/env python3
"""Public first-party TikTok APK distribution diagnostic, no account actions."""
from __future__ import annotations
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

OFFICIAL_PAGE = "https://www.tiktok.com/download"
PACKAGE = "com.zhiliaoapp.musically"

def find_tool(name):
    sdk=Path(os.getenv("ANDROID_HOME","/usr/local/lib/android/sdk"))
    builds=sorted((sdk/"build-tools").glob("*/"+name),reverse=True)
    for tool in builds:
        if tool.is_file() and os.access(tool,os.X_OK): return str(tool)
    return shutil.which(name)

def check_apk(path):
    aapt,apksigner=find_tool("aapt"),find_tool("apksigner")
    if not aapt or not apksigner:
        return "APK_TOOLS_UNAVAILABLE"
    if path.stat().st_size<1_000_000:
        return "APK_TOO_SMALL"
    p=subprocess.run([aapt,"dump","badging",str(path)],capture_output=True,text=True,timeout=20)
    if p.returncode or ("package: name='"+PACKAGE+"'") not in p.stdout:
        return "APK_PACKAGE_MISMATCH"
    v=subprocess.run([apksigner,"verify","--verbose",str(path)],capture_output=True,text=True,timeout=25)
    return "SIGNED_OFFICIAL_PACKAGE_DOWNLOAD" if v.returncode==0 else "APK_SIGNATURE_INVALID"

def main():
    with tempfile.TemporaryDirectory(prefix="tiktok-official-apk-probe-") as temp:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
            try:
                context=browser.new_context(
                    **p.devices["Pixel 7"],locale="pt-BR",accept_downloads=True)
                try:
                    page=context.new_page()
                    try:
                        response=page.goto(OFFICIAL_PAGE,wait_until="commit",timeout=18000)
                        page.wait_for_timeout(7000)
                    except Exception as exc:
                        print("TIKTOK_APK_PROBE="+type(exc).__name__.upper(),flush=True)
                        return 0
                    host=(urllib.parse.urlparse(page.url).hostname or "").lower()
                    status=response.status if response else 0
                    print("TIKTOK_APK_FIRST_PARTY_PAGE_HTTP="+str(status),flush=True)
                    print("TIKTOK_APK_FIRST_PARTY_DOMAIN_OK="+str(host=="tiktok.com" or host.endswith(".tiktok.com")).lower(),flush=True)
                    print("TIKTOK_APK_REDIRECT_HOST="+host[:100],flush=True)
                    if not (host=="tiktok.com" or host.endswith(".tiktok.com")) or status in (401,403,429):
                        print("TIKTOK_APK_PROBE=OFFICIAL_PAGE_UNAVAILABLE",flush=True)
                        return 0
                    actions=page.locator("a,button,[role=button]")
                    choices=actions.evaluate_all("""xs=>xs.filter(x=>{
                      const text=(x.innerText||x.getAttribute('aria-label')||'').toLowerCase();
                      const r=x.getBoundingClientRect();
                      return r.width>0&&r.height>0&&/download apk|baixar apk/.test(text)
                    }).slice(0,10).map(x=>({text:(x.innerText||x.getAttribute('aria-label')||'').trim().slice(0,60),
                      tag:x.tagName}))""")
                    print("TIKTOK_APK_DOWNLOAD_CONTROL_COUNT="+str(len(choices)),flush=True)
                    if not choices:
                        print("TIKTOK_APK_PROBE=OFFICIAL_DOWNLOAD_CONTROL_ABSENT",flush=True)
                        return 0
                    target=actions.filter(has_text=choices[0]["text"]).first
                    try:
                        with page.expect_download(timeout=30000) as event:
                            target.click(timeout=8000)
                        dl=event.value
                        if dl.failure():
                            print("TIKTOK_APK_PROBE=DOWNLOAD_FAILED",flush=True)
                            return 0
                        output=Path(temp)/"official-tiktok.apk"
                        dl.save_as(str(output))
                        print("TIKTOK_APK_PROBE="+check_apk(output),flush=True)
                    except PlaywrightTimeout:
                        print("TIKTOK_APK_PROBE=NO_FILE_DOWNLOAD_EVENT",flush=True)
                    except Exception as exc:
                        print("TIKTOK_APK_PROBE=DOWNLOAD_UI_"+type(exc).__name__.upper(),flush=True)
                    return 0
                finally: context.close()
            finally: browser.close()

if __name__=="__main__":
    try: sys.exit(main())
    except Exception as exc:
        print("TIKTOK_APK_PROBE=SETUP_"+type(exc).__name__.upper(),flush=True)
        sys.exit(1)
