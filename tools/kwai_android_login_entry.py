#!/usr/bin/env python3
"""Select a specific Kwai native login method, never the center of the combined label.

Exit 0: verified credential EditText form. Exit 3: chooser absent.
Exit 4: chooser tapped but form absent. Exit 2: invalid mode or Android UI.
No credentials or UI text are logged.
"""
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from kwai_login_ui_locator import bounds, email_entry, email_form_visible, label, native_chooser_visible

METHODS={"email":re.compile(r"e[ -]?mail",re.I),"phone":re.compile(r"phone|telefone|celular",re.I)}

def method_coords(nodes,method):
    if email_form_visible(nodes):
        return None
    if method=="email":
        return email_entry(nodes)
    pattern=METHODS[method]
    for n in nodes:
        if "login_platform_expand_text" not in (n.get("resource-id") or ""):
            continue
        t=label(n)
        m=pattern.search(t)
        b=bounds(n)
        if not m or not b:continue
        x1,y1,x2,y2=b
        fraction=max(0.08,min(0.92,(m.start()+len(m.group())/2)/max(1,len(t))))
        return round(x1+(x2-x1)*fraction),(y1+y2)//2
    for n in nodes:
        if pattern.fullmatch(label(n)) and bounds(n):
            x1,y1,x2,y2=bounds(n)
            return (x1+x2)//2,(y1+y2)//2
    return None

def adb(*args):
    return subprocess.run(["adb",*args],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=12,check=True).stdout

def snapshot():
    adb("shell","uiautomator","dump","/sdcard/kwai-login-method.xml")
    xml=adb("exec-out","cat","/sdcard/kwai-login-method.xml")
    return list(ET.fromstring(xml).iter("node")), xml.decode("utf-8", "replace")

def tap_bounds(b):
    if not b:
        return False
    x1,y1,x2,y2=b
    adb("shell","input","tap",str((x1+x2)//2),str((y1+y2)//2))
    return True

def clear_interest_onboarding(nodes):
    interest = any(
        (n.get("resource-id") or "").endswith(("interest_tag_fragment_container","interest_tag_container"))
        for n in nodes
    ) or any("select your interests" in label(n).lower() for n in nodes)
    if not interest:
        return False
    for n in nodes:
        if (n.get("resource-id") or "").endswith("bt_interest_skip_top_right") and tap_bounds(bounds(n)):
            print("KWAI_INTEREST_ONBOARDING_SKIPPED")
            time.sleep(3)
            return True
    for n in nodes:
        if re.fullmatch(r"skip|pular",label(n).strip(),re.I) and tap_bounds(bounds(n)):
            print("KWAI_INTEREST_ONBOARDING_SKIPPED")
            time.sleep(3)
            return True
    return False

def main():
    method=sys.argv[1] if len(sys.argv)==2 else "auto"
    if method=="auto":
        forced=os.getenv("KWAI_LOGIN_METHOD","").strip().lower()
        if forced in METHODS:
            method=forced
        else:
            login=os.getenv("KWAI_LOGIN","").strip()
            digits=re.sub(r"[^0-9+]","",login)
            method="phone" if login and digits==login and len(re.sub(r"\D","",login))>=8 else "email"
    if method not in METHODS:
        return 2
    try:
        nodes, xml_text=snapshot()
        for _ in range(3):
            if not clear_interest_onboarding(nodes):
                break
            nodes, xml_text=snapshot()
        if email_form_visible(nodes):
            print("KWAI_NATIVE_LOGIN_FORM_ALREADY_VISIBLE")
            return 0
        for _ in range(6):
            if email_form_visible(nodes) or native_chooser_visible(nodes,xml_text):
                break
            time.sleep(1)
            nodes, xml_text=snapshot()
        if email_form_visible(nodes):
            print("KWAI_NATIVE_LOGIN_FORM_ALREADY_VISIBLE")
            return 0
        if not native_chooser_visible(nodes,xml_text):
            print("KWAI_NATIVE_LOGIN_CHOOSER_ABSENT")
            return 3
        coords=method_coords(nodes,method) or (email_entry(nodes,xml_text) if method=="email" else None)
        if not coords:
            print("KWAI_NATIVE_LOGIN_METHOD_NOT_FOUND")
            return 3
        adb("shell","input","tap",str(coords[0]),str(coords[1]))
        print("KWAI_NATIVE_LOGIN_METHOD_TAPPED="+method.upper())
        for _ in range(5):
            time.sleep(1)
            nodes, xml_text=snapshot()
            if email_form_visible(nodes):
                print("KWAI_NATIVE_LOGIN_FORM_VISIBLE")
                return 0
            if clear_interest_onboarding(nodes):
                nodes, xml_text=snapshot()
                coords=method_coords(nodes,method) or (email_entry(nodes,xml_text) if method=="email" else None)
                if coords:
                    adb("shell","input","tap",str(coords[0]),str(coords[1]))
    except (subprocess.CalledProcessError,subprocess.TimeoutExpired,OSError,ET.ParseError):
        print("KWAI_NATIVE_LOGIN_UI_UNAVAILABLE")
        return 2
    print("KWAI_NATIVE_LOGIN_METHOD_NO_FORM")
    return 4

if __name__=="__main__":
    raise SystemExit(main())
