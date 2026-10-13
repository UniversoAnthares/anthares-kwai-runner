#!/usr/bin/env python3
"""Privacy-safe Kwai UI triage: aggregate flags only, never raw XML or UI text."""
import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path

OFFLINE = re.compile(r"un_connected_network|no internet|network error|connection failed|offline|sem conex[aã]o|sem internet|erro de rede", re.I)
ERROR = re.compile(r"system error|try again later|something went wrong|erro do sistema|tente novamente", re.I)
VERIFY = re.compile(r"captcha|verification|verifica[cç][aã]o|robot|rob[oô]", re.I)
LOGIN = re.compile(r"log[ -]?in|sign[ -]?in|entrar|fazer login", re.I)


def summarize(xml):
    root = ET.fromstring(xml)
    nodes = list(root.iter("node"))
    def rid(n):
        return (n.get("resource-id") or "").split("/")[-1]
    def label(n):
        return (n.get("text") or "") + " " + (n.get("content-desc") or "")
    from kwai_login_ui_locator import login_surface_kind
    return {
        "nodes": len(nodes),
        "kwai_nodes": sum("com.kwai.video" in (n.get("package") or "") for n in nodes),
        "clickable_nodes": sum(n.get("clickable") == "true" for n in nodes),
        "webview": int(any((n.get("class") or "").endswith("WebView") for n in nodes)),
        "offline_hint": int(any(OFFLINE.search(rid(n) + " " + label(n)) for n in nodes)),
        "system_error_hint": int(any(ERROR.search(label(n)) for n in nodes)),
        "verification_hint": int(any(VERIFY.search(label(n)) for n in nodes)),
        "login_label_hint": int(any(LOGIN.search(label(n)) for n in nodes)),
        "permission_dialog": int(any("permissioncontroller" in (n.get("package") or "") for n in nodes)),
        "continue_gate": int(any("signin_fre_continue_button" in rid(n) for n in nodes)),
        "profile_tab": int(any(rid(n) == "id_home_bottom_tab_me" for n in nodes)),
        "login_surface": login_surface_kind(nodes, xml),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", default=".")
    args = parser.parse_args()
    files = sorted(Path(args.directory).glob("semantic-*.xml"))
    if not files:
        print("KWAI_TRIAGE_XML_AVAILABLE=0")
        return 0
    files.sort(key=lambda p: p.stat().st_mtime)
    for i, file in enumerate(files[-4:]):
        try:
            summary = summarize(file.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ET.ParseError):
            print(f"KWAI_TRIAGE_FRAME_{i}=UNREADABLE")
            continue
        print(f"KWAI_TRIAGE_FRAME_{i}=" + " ".join(f"{k}:{v}" for k, v in summary.items()))
    print("KWAI_TRIAGE_RAW_UI_EXPORTED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
