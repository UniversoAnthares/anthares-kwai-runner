#!/usr/bin/env python3
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import re

AUTH = (
    "log in","login","entrar","sign in",
    "password","senha",
    "verification code","código de verificação",
    "phone number","número de telefone",
    "continue with google","continuar com google",
    "continue with facebook","continuar com facebook"
)
DYNAMIC = (
    "resource downloading",
    "access to all the features when",
    "hang in there",
)

def adb(*args):
    return subprocess.run(
        ["adb", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=25,
    ).stdout

def dump():
    adb("shell","uiautomator","dump","/sdcard/kwai-auth.xml")
    adb("pull","/sdcard/kwai-auth.xml","/tmp/kwai-auth.xml")
    root=ET.parse("/tmp/kwai-auth.xml").getroot()
    nodes=list(root.iter("node"))
    text=" ".join(
        ((n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).strip())
        for n in nodes
    ).lower()
    return root, nodes, text

def center(bounds):
    m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds or "")
    if not m:
        return None
    x1,y1,x2,y2=map(int,m.groups())
    return (x1+x2)//2,(y1+y2)//2

def tap(node):
    pos=center(node.attrib.get("bounds",""))
    if not pos:
        return False
    adb("shell","input","tap",str(pos[0]),str(pos[1]))
    time.sleep(2)
    return True

def strong_authenticated(text, nodes):
    strong=(
        "log out","logout","sair","sign out",
        "my profile","meu perfil",
    )
    if any(x in text for x in strong):
        return True
    expected=os.getenv("KWAI_EXPECTED_ACCOUNT","").strip().casefold()
    if expected and expected in text:
        return True
    # Never treat generic main navigation, feed authors, or create buttons as
    # proof of authentication. They also exist in anonymous MAIN state.
    return False

def inspect_profile_for_identity():
    expected=os.getenv("KWAI_EXPECTED_ACCOUNT","").strip()
    for _ in range(18):
        try:
            root,nodes,text=dump()
        except Exception:
            time.sleep(2)
            continue
        if any(x in text for x in AUTH):
            print("KWAI_AUTH_STATE=AUTH_REQUIRED")
            return 10
        if strong_authenticated(text,nodes):
            print("KWAI_AUTH_STATE=AUTHENTICATED_UI")
            return 0
        if any(x in text for x in DYNAMIC):
            time.sleep(2)
            continue
        time.sleep(1)
    return 11

for _ in range(12):
    try:
        root,nodes,text=dump()
    except Exception:
        time.sleep(2)
        continue
    if any(x in text for x in AUTH):
        print("KWAI_AUTH_STATE=AUTH_REQUIRED")
        sys.exit(10)
    # Do not accept identity markers from feed cards or third-party profiles.
    # Authentication can only be accepted after navigating to own Profile.
    # Anonymous MAIN is intentionally inconclusive. Use the proven semantic
    # Profile route to seek explicit account identity, while respecting dynamic
    # module loading and refusing to turn loading/timeouts into auth proof.
    profile_node=None
    for n in nodes:
        if n.attrib.get("resource-id","").endswith("ll_profile") and n.attrib.get("clickable","")=="true":
            profile_node=n
            break
    if profile_node and tap(profile_node):
        rc=inspect_profile_for_identity()
        if rc in (0,10):
            sys.exit(rc)
        break
    time.sleep(2)

print("KWAI_AUTH_STATE=UNKNOWN")
sys.exit(11)
