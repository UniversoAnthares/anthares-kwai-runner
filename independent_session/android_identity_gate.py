#!/usr/bin/env python3
"""Fail-closed independent authenticated identity gate for Android UI XML.
Only an exact account handle on a logged-in profile screen is acceptable.
No credentials, tokens, screenshots or XML are ever printed.
"""
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

LOGIN_MARKERS=("log in","sign in","login","sign up","continue with google","entrar","fazer login","cadastrar","iniciar sesión")
PROFILE_MARKERS=("edit profile","editar perfil","edit your profile","editar o perfil")
def verify(xml: bytes, expected: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]{2,64}",expected):
        raise ValueError("INVALID_EXPECTED_HANDLE")
    if len(xml)>2_000_000:
        raise ValueError("UI_TOO_LARGE")
    root=ET.fromstring(xml)
    nodes=list(root.iter("node"))
    if not nodes:
        raise ValueError("UI_EMPTY")
    texts=[(n.get("text","")+" "+n.get("content-desc","")).strip().casefold() for n in nodes]
    expected=expected.casefold()
    exact=any(re.search(r"(?<![\w.-])@?"+re.escape(expected)+r"(?![\w.-])",t) for t in texts)
    profile=any(any(marker in t for marker in PROFILE_MARKERS) for t in texts)
    login=any(any(marker in t for marker in LOGIN_MARKERS) for t in texts)
    if not exact:
        raise ValueError("ACCOUNT_HANDLE_NOT_VISIBLE")
    if not profile:
        raise ValueError("AUTHENTICATED_PROFILE_CONTROL_NOT_VISIBLE")
    if login:
        raise ValueError("LOGIN_CONTROL_VISIBLE")
    return "AUTH_IDENTITY_UI_VERIFIED"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("xml_path")
    p.add_argument("--account",required=True)
    args=p.parse_args()
    try:
        result=verify(Path(args.xml_path).read_bytes(),args.account)
    except (ValueError,ET.ParseError,OSError) as exc:
        print("AUTH_IDENTITY_GATE=REJECTED:"+str(exc),file=sys.stderr)
        return 1
    print(result)
    return 0
if __name__=="__main__":sys.exit(main())
