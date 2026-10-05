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

# Clear common onboarding screens without resetting app data.
for _ in range(8):
    dismiss_android_permission_dialogs()
    r=dump(); txt=" ".join(label(n) for n in nodes(r))
    if any(k in txt for k in ("log in","login","entrar","sign in","telefone","phone","email")): break
    if tap_matching(("skip","pular","later","agora não","continue","continuar","next","próximo")): continue
    # Interest selection: choose Education/Talent/Entertainment if shown.
    if tap_matching(("education","talent & art","entertainment")): continue
    adb("shell","input","keyevent","4"); time.sleep(1)

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
