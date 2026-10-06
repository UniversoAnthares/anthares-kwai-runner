#!/usr/bin/env python3
import os, subprocess, time, xml.etree.ElementTree as ET

LOGIN=os.environ.get("KWAI_LOGIN","")
PASSWORD=os.environ.get("KWAI_PASSWORD","")
if not LOGIN or not PASSWORD:
    raise SystemExit(2)

def adb(*args, input_text=None):
    return subprocess.run(["adb",*args], input=input_text, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=25).stdout

def dump():
    adb("shell","uiautomator","dump","/sdcard/kwai-login.xml")
    adb("pull","/sdcard/kwai-login.xml","/tmp/kwai-login.xml")
    return ET.parse("/tmp/kwai-login.xml").getroot()

def center(bounds):
    import re
    m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds or "")
    if not m: raise ValueError("bad bounds")
    x1,y1,x2,y2=map(int,m.groups())
    return (x1+x2)//2,(y1+y2)//2

def tap_node(n):
    b=n.attrib.get("bounds","")
    if b:
        x,y=center(b); adb("shell","input","tap",str(x),str(y)); time.sleep(1); return True
    return False

def nodes(root):
    return list(root.iter("node"))

def label(n):
    return (n.attrib.get("text","")+" "+n.attrib.get("content-desc","")).lower()

def tap_matching(words):
    r=dump()
    for n in nodes(r):
        s=label(n)
        if any(w in s for w in words) and tap_node(n): return True
    return False

def editable_nodes(r):
    return [n for n in nodes(r) if n.attrib.get("class","").endswith("EditText") or n.attrib.get("editable","")=="true"]

def fill(value, index=0):
    r=dump()
    edits=editable_nodes(r)
    if len(edits) <= index: return False
    tap_node(edits[index])
    adb("shell","input","keyevent","KEYCODE_MOVE_END")
    # Send through stdin to adb shell; secrets are never printed by this program.
    safe=value.replace("%","%25").replace(" ","%s").replace("&","\\&").replace("(","\\(").replace(")","\\)")
    adb("shell","input","text",safe)
    time.sleep(.7)
    return True



def tap_resource_id(suffix):
    r=dump()
    for n in nodes(r):
        rid=n.attrib.get("resource-id","")
        if rid.endswith(suffix) and tap_node(n):
            return True
    return False

def clear_interest_discovery():
    # Current Kwai onboarding uses icon-only like/dislike controls for 11 cards.
    # Resource IDs are stable even though the buttons have no text/content-desc.
    for _ in range(15):
        r=dump()
        ids={n.attrib.get("resource-id","") for n in nodes(r)}
        if not any(x.endswith("tiny_discovery_like_button") or x.endswith("tiny_discovery_dislike_button") for x in ids):
            return
        if not tap_resource_id("tiny_discovery_dislike_button"):
            tap_resource_id("tiny_discovery_like_button")
        time.sleep(.6)

def dismiss_android_permission_dialogs():
    # Runtime permission dialogs are owned by Android, not Kwai. Clear them before
    # looking for Kwai controls. Denying notifications is safe for publishing/login.
    for _ in range(8):
        r=dump()
        ns=nodes(r)
        packages={n.attrib.get("package","") for n in ns}
        if not any("permissioncontroller" in p for p in packages):
            return
        acted=False
        for words in (("don’t allow","don't allow","not now","agora não","não permitir"),
                      ("allow","permitir","while using the app","durante o uso do app")):
            for n in ns:
                if any(w in label(n) for w in words) and tap_node(n):
                    acted=True
                    break
            if acted: break
        if not acted:
            adb("shell","input","keyevent","4")
            time.sleep(1)

dismiss_android_permission_dialogs()
clear_interest_discovery()
# Normalize the current chooser into the Phone authentication surface when present.
subprocess.run(["python3","kwai_phone_surface_probe.py"],check=False)
time.sleep(2)
# Stabilization matrix showed restart-after-nav is the strongest causal path.

def reach_profile_semantically():
    # Probe 37378176856 proved that adaptive horizontal traversal can expose
    # Home / Discover / Inbox / Profile. Prefer the semantic Profile node.
    for _ in range(14):
        r=dump()
        txt=" ".join(label(n) for n in nodes(r))
        if "profile" in txt and ("home" in txt or "discover" in txt or "inbox" in txt):
            for n in nodes(r):
                if "profile" in label(n) and tap_node(n):
                    time.sleep(2)
                    return True
        # Advance onboarding cards without assuming a fixed 11/12-card count.
        adb("shell","input","swipe","850","1100","180","1100","250")
        time.sleep(.8)
        clear_interest_discovery()
    return False

# Clear common onboarding screens without resetting app data.
for _ in range(8):
    dismiss_android_permission_dialogs()
    clear_interest_discovery()
    r=dump(); txt=" ".join(label(n) for n in nodes(r))
    if any(k in txt for k in ("log in","login","entrar","sign in","telefone","phone","email")): break
    if tap_matching(("skip","pular","later","agora não","continue","continuar","next","próximo")): continue
    # Interest selection: choose Education/Talent/Entertainment if shown.
    if tap_matching(("education","talent & art","entertainment")): continue
    adb("shell","input","keyevent","4"); time.sleep(1)

# If onboarding did not expose login directly, use the proven path to the
# main navigation and open Profile semantically.
r=dump(); txt=" ".join(label(n) for n in nodes(r))
if not any(k in txt for k in ("log in","login","entrar","sign in","telefone","phone","email")):
    if reach_profile_semantically():
        adb("shell","am","force-stop","com.kwai.video"); time.sleep(2)
        adb("shell","monkey","-p","com.kwai.video","-c","android.intent.category.LAUNCHER","1"); time.sleep(15)
        reach_profile_semantically()

tap_matching(("log in","login","entrar","sign in"))
time.sleep(1)
# Prefer password/email/phone login over social providers.
tap_matching(("password","senha","phone","telefone","email","e-mail"))
time.sleep(1)
if not fill(LOGIN):
    # Some Kwai builds expose the account field only after choosing the generic login method.
    tap_matching(("other ways","other login","use phone","use email","phone number","mobile","account","outras formas","outra forma","usar telefone","usar e-mail","número de telefone","conta"))
    time.sleep(1)
    if not fill(LOGIN):
        # Last deterministic fallback: focus the lower-center form area and verify an editable field appeared.
        adb("shell","input","tap","540","1120"); time.sleep(1)
        if not fill(LOGIN): raise SystemExit(3)
# Move to password step if needed.
tap_matching(("next","continue","continuar","avançar"))
time.sleep(1)
r=dump(); edits=editable_nodes(r)
if len(edits)>=2:
    if not fill(PASSWORD, 1): raise SystemExit(4)
elif not fill(PASSWORD, 0):
    raise SystemExit(4)
tap_matching(("log in","login","entrar","sign in","continue","continuar"))
time.sleep(4)
# Success means the password form disappeared. Challenges remain interactive.
r=dump(); txt=" ".join(label(n) for n in nodes(r))
if any(k in txt for k in ("incorrect password","senha incorreta","wrong password")): raise SystemExit(5)
if any(k in txt for k in ("verification code","código de verificação","captcha","verify it's you","confirme")): raise SystemExit(6)
if any(k in txt for k in ("password","senha")) and any(k in txt for k in ("log in","login","entrar")): raise SystemExit(7)
print("KWAI_AUTO_LOGIN_UI_ADVANCED")
