#!/usr/bin/env python3
"""Classify Kwai UIAutomator XML into stable semantic states and candidate actions."""
import argparse,json,re,xml.etree.ElementTree as ET
from pathlib import Path

AUTH_WORDS=("log in","login","sign in","entrar","password","senha","verification code","código de verificação","phone number","número de telefone")
CREATE_PROFILE=("create your profile","crie seu perfil","continue with google","continuar com google")
PROFILE_WORDS=("profile","perfil","followers","following","seguidores","seguindo")
FEED_WORDS=("home","início","inicio","for you","para você","following","seguindo")

def center(bounds):
    m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",bounds or "")
    if not m:return None
    x1,y1,x2,y2=map(int,m.groups())
    return [(x1+x2)//2,(y1+y2)//2]

def parse(xml_text,expected=""):
    root=ET.fromstring(xml_text)
    nodes=list(root.iter("node"))
    items=[]
    for n in nodes:
        text=" ".join(filter(None,[n.get("text",""),n.get("content-desc",""),n.get("resource-id","")])).strip()
        if text:items.append(text)
    blob=" ".join(items).casefold()
    expected=expected.strip().lstrip("@").casefold()
    # A username typed into a login form or shown in a feed is NOT proof
    # of an authenticated account. Require visible, non-editable profile UI.
    static_labels=" ".join(
        " ".join(filter(None,[n.get("text",""),n.get("content-desc","")]))
        for n in nodes if not (n.get("class","").endswith("EditText"))
    ).casefold()
    login_visible=any(x in blob for x in AUTH_WORDS)
    onboarding_visible=any(x in blob for x in CREATE_PROFILE)
    profile_context=any(x in static_labels for x in ("profile","perfil","followers","following","seguidores","seguindo"))
    identity=bool(expected and profile_context and not login_visible and not onboarding_visible
                  and re.search(r"(?<![a-z0-9_.])@?"+re.escape(expected)+r"(?![a-z0-9_.])",static_labels))
    if onboarding_visible: state="CREATE_PROFILE"
    elif login_visible: state="AUTH_REQUIRED"
    elif identity: state="AUTHENTICATED_PROFILE"
    elif any(x in blob for x in PROFILE_WORDS): state="PROFILE_UNKNOWN"
    elif any(x in blob for x in FEED_WORDS): state="FEED"
    else: state="UNKNOWN"
    actions=[]
    patterns={"google":r"continue with google|continuar com google|\bgoogle\b","email":r"\be-?mail\b|endereço de e-mail","phone":r"\bphone\b|telefone","profile":r"\bprofile\b|\bperfil\b"}
    for name,pat in patterns.items():
        for n in nodes:
            label=" ".join([n.get("text",""),n.get("content-desc","")]).strip()
            if re.search(pat,label,re.I):
                c=center(n.get("bounds",""))
                if c: actions.append({"action":name,"center":c,"label":label});break
    return {"schema":"anthares.mobile.ui-state.v1","state":state,"identity_verified":identity,"actions":actions}

def main():
    p=argparse.ArgumentParser();p.add_argument("xml");p.add_argument("--expected",default="");p.add_argument("--action",choices=("google","email","phone","profile"))
    a=p.parse_args();result=parse(Path(a.xml).read_text(encoding="utf-8",errors="replace"),a.expected)
    if a.action:
        match=next((x for x in result["actions"] if x["action"]==a.action),None)
        if not match:return 1
        print(*match["center"]);return 0
    print(json.dumps(result,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
