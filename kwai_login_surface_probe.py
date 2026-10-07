#!/usr/bin/env python3
"""Non-credentialed Kwai login surface probe.
Instruments the UI tree after MAIN/Profile to discover the real login entrypoint.
No credentials are used. Records text/resource-id/class/clickable/bounds per transition.
"""
import subprocess, time, xml.etree.ElementTree as ET, os, json

adb = lambda *a: subprocess.run(["adb",*a], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=20).stdout

def dump():
    # Causal repair (finding 20261006-2252): the dump target and the read-back path
    # must be identical. The previous version dumped kwai-login-probe.xml but read
    # kwai-login.xml, so every snapshot parsed as empty and logged state=OTHER.
    target = "/sdcard/kwai-login-probe.xml"
    for _ in range(3):
        adb("shell", "uiautomator", "dump", target)
        raw = adb("shell", "cat", target)
        if raw.strip().startswith("<"):
            try:
                return ET.fromstring(raw)
            except Exception:
                pass
        time.sleep(1)
    return None

def nodes(root):
    return list(root.iter("node")) if root is not None else []

def node_info(n):
    return {
        "text": n.attrib.get("text",""),
        "content_desc": n.attrib.get("content-desc",""),
        "class": n.attrib.get("class",""),
        "resource_id": n.attrib.get("resource-id",""),
        "clickable": n.attrib.get("clickable",""),
        "editable": n.attrib.get("editable",""),
        "bounds": n.attrib.get("bounds",""),
    }

def state_from_text(t):
    t_low = t.lower()
    if "permissioncontroller" in t_low:
        return "PERMISSION"
    if "start now" in t_low or "you're all set" in t_low or "tudo pronto" in t_low:
        return "START"
    if "resource downloading" in t_low:
        return "RESOURCE_LOADING"
    # Preparation gate observed in run 37529160444 (finding 20261006-2241): Kwai
    # blocks the UI on a download modal ("Skip the preparation?" / "Sorry, the
    # internet's a bit slow. Hang in there!") before any login surface exists.
    if ("skip the preparation" in t_low or "hang in there" in t_low
            or "internet's a bit slow" in t_low or "preparation" in t_low):
        return "RESOURCE_LOADING"
    if "profile" in t_low and ("home" in t_low or "discover" in t_low or "inbox" in t_low):
        return "MAIN"
    if "choose like or dislike" in t_low:
        return "INTEREST"
    if "select your interests" in t_low and ("skip" in t_low or "selected and continue" in t_low):
        return "INTEREST_SELECT"
    if "pixel launcher isn't responding" in t_low or "isn't responding" in t_low:
        return "LAUNCHER_ANR"
    return "OTHER"

def tap_node(n):
    b = n.attrib.get("bounds","")
    import re
    m = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", b or "")
    if not m:
        return False
    x1,y1,x2,y2 = map(int, m.groups())
    x, y = (x1+x2)//2, (y1+y2)//2
    adb("shell","input","tap",str(x),str(y))
    time.sleep(1.5)
    return True

def tap_matching(words):
    root = dump()
    for n in nodes(root):
        label = (n.attrib.get("text","") + " " + n.attrib.get("content-desc","")).lower()
        if any(w in label for w in words) and n.attrib.get("clickable","") == "true":
            if tap_node(n):
                return True
    return False

def rid(ns, suffix):
    for n in ns:
        if n.attrib.get("resource-id","").endswith(suffix):
            return n
    return None

def snapshot(label):
    root = dump()
    ns = nodes(root)
    txt = " ".join((n.attrib.get("text","") + " " + n.attrib.get("content-desc","")).lower() for n in ns)
    s = state_from_text(txt)
    out = {
        "label": label,
        "state": s,
        "text_preview": txt[:500],
        "editable_nodes": [node_info(n) for n in ns if n.attrib.get("editable","") == "true" or n.attrib.get("class","").endswith("EditText")],
        "login_like_nodes": [node_info(n) for n in ns if any(k in (n.attrib.get("text","") + " " + n.attrib.get("content-desc","")).lower() for k in ("log in","login","entrar","sign in","phone","telefone","email","e-mail","senha","password","code","código","verify","verificar"))],
        "resource_ids": sorted({n.attrib.get("resource-id","") for n in ns if n.attrib.get("resource-id","")}),
    }
    print(f"[PROBE] {label} state={s} editables={len(out['editable_nodes'])} login_like={len(out['login_like_nodes'])}")
    return out

# Force-stop and relaunch Kwai
adb("shell","am","force-stop","com.kwai.video")
time.sleep(2)
adb("shell","monkey","-p","com.kwai.video","-c","android.intent.category.LAUNCHER","1")
time.sleep(10)

probe_log = []

# Phase 1: permissions/onboarding
for i in range(12):
    s = snapshot(f"onboarding-{i}")
    probe_log.append(s)
    if s["state"] == "PERMISSION":
        n = rid(nodes(dump()), "permission_deny_button")
        if n is None:
            n = rid(nodes(dump()), "permission_allow_button")
        if n is not None:
            tap_node(n)
            time.sleep(1)
        continue
    if s["state"] == "START":
        tap_matching(("start now","começar agora","iniciar agora"))
        time.sleep(2)
        continue
    if s["state"] == "INTEREST":
        n = rid(nodes(dump()), "tiny_discovery_dislike_button")
        if n is None:
            n = rid(nodes(dump()), "tiny_discovery_like_button")
        if n is not None:
            tap_node(n)
        else:
            adb("shell","input","swipe","850","1100","180","1100","250")
        time.sleep(1)
        continue
    if s["state"] == "INTEREST_SELECT":
        n = None
        for x in nodes(dump()):
            label = (x.attrib.get("text","") + " " + x.attrib.get("content-desc","")).strip().lower()
            if label == "skip" or label.startswith("skip "):
                n = x
                break
        if n is not None:
            tap_node(n)
        else:
            adb("shell","input","tap","90","250")
        time.sleep(2)
        continue
    if s["state"] == "RESOURCE_LOADING":
        # Preparation gate (finding 20261006-2241): prefer waiting a bounded time
        # for the resource download; if it is stuck (observed at 5%), accept the
        # modal's own "Yes, skip" and continue to the real UI.
        stuck = 0
        for _ in range(10):
            time.sleep(3)
            s2 = snapshot("resource-wait")
            probe_log.append(s2)
            txt2 = s2["text_preview"]
            if "resource downloading" not in txt2 and "hang in there" not in txt2 \
               and "skip the preparation" not in txt2 and "internet's a bit slow" not in txt2:
                break
            stuck += 1
        if stuck >= 10:
            if tap_matching(("yes, skip", "yes skip")):
                time.sleep(3)
            else:
                tap_matching(("skip", "pular"))
                time.sleep(3)
        continue
    if s["state"] == "LAUNCHER_ANR":
        n = rid(nodes(dump()), "aerr_close")
        if n is None:
            n = rid(nodes(dump()), "aerr_wait")
        if n is not None:
            tap_node(n)
        adb("shell","input","keyevent","3")
        time.sleep(3)
        adb("shell","am","force-stop","com.kwai.video")
        time.sleep(1)
        adb("shell","monkey","-p","com.kwai.video","1")
        time.sleep(8)
        continue
    if s["state"] == "MAIN":
        break
    if any(k in s["text_preview"] for k in ("log in","login","entrar","sign in","phone","telefone","email")):
        break
    # Generic advance
    adb("shell","input","swipe","850","1100","180","1100","250")
    time.sleep(1)

# Phase 2: from MAIN/Profile, instrument transitions
for i in range(10):
    root = dump()
    ns = nodes(root)
    txt = " ".join((n.attrib.get("text","") + " " + n.attrib.get("content-desc","")).lower() for n in ns)
    s = state_from_text(txt)
    snap = snapshot(f"main-{i}")
    probe_log.append(snap)
    if any(k in txt for k in ("log in","login","entrar","sign in","phone","telefone","email","verification code","código de verificação","profile","meu perfil","my profile")):
        break
    # Try tapping Profile if visible
    profile_node = None
    for n in ns:
        label = (n.attrib.get("text","") + " " + n.attrib.get("content-desc","")).lower()
        if "profile" in label and n.attrib.get("clickable","") == "true":
            profile_node = n
            break
    if profile_node is not None:
        tap_node(profile_node)
        time.sleep(2)
        continue
    adb("shell","input","swipe","850","1100","180","1100","250")
    time.sleep(1)

# Save probe log where the workflow artifact path expects it (repo root);
# the previous RUNNER_TEMP location meant kwai-login-probe-log.json was never
# uploaded (finding 20261006-2252). Also emit an explicit validity signal so an
# empty-tree run can never be mistaken for a valid negative again.
out_path = os.path.join(os.getcwd(), "kwai-login-probe-log.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(probe_log, f, ensure_ascii=False, indent=2)
print(f"[PROBE] log saved to {out_path}")
observed = [e for e in probe_log if e.get("resource_ids") or e.get("editable_nodes") or e.get("login_like_nodes") or e.get("text_preview")]
if not observed:
    print("[PROBE] TEST_VALIDITY=INVALID no UI tree was read")
    raise SystemExit(3)
print(f"[PROBE] TEST_VALIDITY=OK snapshots={len(probe_log)} observed={len(observed)}")
print("[PROBE] final editable nodes and login-like nodes:")
found = False
for entry in probe_log:
    if entry["editable_nodes"] or entry["login_like_nodes"]:
        found = True
        print(json.dumps({"label": entry["label"], "state": entry["state"],
                          "editables": entry["editable_nodes"],
                          "login_like": entry["login_like_nodes"]}, ensure_ascii=False, indent=2))
if not found:
    print("[PROBE] no editable/login-like nodes in any phase")
