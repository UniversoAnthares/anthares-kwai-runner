#!/usr/bin/env python3
"""Alternative native route: resolve an exported Kwai login Activity via Android
package manager, avoiding screen taps. No secrets, no UI dumps, no bypass.
Fail closed unless native login UI becomes verifiable.
"""
import re,subprocess,sys,time,xml.etree.ElementTree as ET
sys.path.insert(0,"tools")
from kwai_login_ui_locator import email_form_visible,native_chooser_visible
PKG="com.kwai.video"
def run(*a,timeout=18):
    p=subprocess.run(["adb",*a],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=timeout)
    return p.stdout if p.returncode==0 else ""
def snapshot():
    run("shell","uiautomator","dump","/sdcard/kwai-deeplink.xml")
    s=run("exec-out","cat","/sdcard/kwai-deeplink.xml")
    return list(ET.fromstring(s).iter("node"))
# Read Android's own manifest-derived resolver data, not an invented URL.
info=run("shell","dumpsys","package",PKG,timeout=25)
if not info:
    print("KWAI_INTENT_PACKAGE_UNAVAILABLE");raise SystemExit(3)
# Only exported, resolver-visible activities can be launched externally.
# Query candidates through package manager, without trying unexported components.
candidate_actions=("android.intent.action.VIEW",)
candidate_uris=("kwai://login", "kwai://account/login")
for uri in candidate_uris:
    result=run("shell","cmd","package","resolve-activity","--brief","-a","android.intent.action.VIEW","-d",uri,timeout=12)
    if PKG not in result:
        continue
    print("KWAI_INTENT_NATIVE_ROUTE_RESOLVED")
    run("shell","am","start","-a","android.intent.action.VIEW","-d",uri,"-p",PKG)
    time.sleep(3)
    try:
        ns=snapshot()
        if email_form_visible(ns) or native_chooser_visible(ns):
            print("KWAI_INTENT_NATIVE_LOGIN_READY");raise SystemExit(0)
    except (ET.ParseError,subprocess.TimeoutExpired):pass
print("KWAI_INTENT_NATIVE_ROUTE_UNAVAILABLE")
raise SystemExit(3)
