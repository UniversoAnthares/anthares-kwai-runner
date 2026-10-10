#!/usr/bin/env python3
"""Read-only native Kwai UI selector. Emits no UI text, secrets, or session data."""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from anthares_mobile.ui_state import parse as semantic_parse

BOUNDS = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")
EMAIL = re.compile(r"e[ -]?mail|correio eletr[oô]nico", re.I)
LOGIN_CONTEXT = re.compile(
    r"log[ -]?in|sign[ -]?in|entrar|password|senha|verification|verifica[cç][aã]o|"
    r"phone number|n[uú]mero de telefone|e[ -]?mail|account login",
    re.I,
)
CREDENTIAL_FIELD = re.compile(
    r"password|senha|email|e-mail|phone|telefone|username|login|verify|verification|code|c[oó]digo",
    re.I,
)


def parse(xml_text):
    root = ET.fromstring(xml_text)
    return list(root.iter("node"))


def label(node):
    return " ".join((node.get("text") or "", node.get("content-desc") or "")).strip()


def bounds(node):
    match = BOUNDS.fullmatch(node.get("bounds") or "")
    if not match:
        return None
    x1, y1, x2, y2 = map(int, match.groups())
    if x1 >= x2 or y1 >= y2:
        return None
    return x1, y1, x2, y2


def semantic_action(xml_text,name):
    try:
        state=semantic_parse(xml_text)
    except Exception:
        return None
    action=next((a for a in state.get("actions",[]) if a.get("action")==name),None)
    return tuple(action["center"]) if action and action.get("center") else None


def email_form_visible(nodes):
    fields = [n for n in nodes if (n.get("class") or "").endswith("EditText")]
    if not fields:
        return False
    if any(CREDENTIAL_FIELD.search(" ".join((
        label(n), n.get("resource-id") or "", n.get("hint") or ""
    ))) for n in fields):
        return True
    context = " ".join(label(n) for n in nodes)
    return len(fields) >= 2 and bool(LOGIN_CONTEXT.search(context))


def native_chooser_visible(nodes,xml_text=""):
    # A credential form is not the chooser, even if semantic email action exists.
    if email_form_visible(nodes):
        return False
    if any(
        "login_platform_expand_text" in (n.get("resource-id") or "")
        and EMAIL.search(label(n))
        and bounds(n)
        for n in nodes
    ):
        return True
    return any(not (n.get("class") or "").endswith("EditText") and EMAIL.fullmatch(label(n)) and bounds(n) for n in nodes) or (semantic_action(xml_text,"email") is not None and not any((n.get("class") or "").endswith("EditText") for n in nodes))


def email_entry(nodes,xml_text=""):
    if email_form_visible(nodes):
        return None
    for node in nodes:
        if "login_platform_expand_text" not in (node.get("resource-id") or ""):
            continue
        text = label(node)
        match = EMAIL.search(text)
        b = bounds(node)
        if not match or not b:
            continue
        x1, y1, x2, y2 = b
        fraction = (match.start() + len(match.group()) / 2) / max(len(text), 1)
        fraction = max(0.08, min(0.92, fraction))
        return round(x1 + (x2 - x1) * fraction), (y1 + y2) // 2
    for node in nodes:
        if EMAIL.fullmatch(label(node)) and bounds(node):
            x1, y1, x2, y2 = bounds(node)
            return (x1 + x2) // 2, (y1 + y2) // 2
    return semantic_action(xml_text,"email")


def google_entry(nodes,xml_text=""):
    for node in nodes:
        if "login_platform_item_layout" in (node.get("resource-id") or "") and bounds(node):
            x1, y1, x2, y2 = bounds(node)
            return (x1 + x2) // 2, (y1 + y2) // 2
    return semantic_action(xml_text,"google")


def profile_tab(nodes,xml_text=""):
    """Locate the real navigation target without treating a profile heading as a tab.

    Prefer a bounded, clickable ancestor for profile-related resource IDs. Some
    builds expose the child outside the bottom band while the clickable parent
    is the actual tab. Never tap account content, headings, or login forms.
    """
    if email_form_visible(nodes):
        return None
    height=max((bounds(n)[3] for n in nodes if bounds(n)),default=0)
    if height < 500:
        return None
    explicit=("id_home_bottom_tab_me","ll_profile","tab_profile","btn_profile")
    forbidden=("avatar","image","photo","header","title","edit","follow","setting",
               "create_profile","profile_name","profile_user","profile_info")
    candidates=[]
    for node in nodes:
        rid=(node.get("resource-id") or "").casefold().split("/")[-1]
        b=bounds(node)
        if not b or any(w in rid for w in forbidden):
            continue
        text=label(node).casefold().strip()
        is_explicit=rid in explicit
        is_profile=("profile" in rid or rid.endswith("_me")) and not is_explicit
        is_label=text in ("profile","perfil","me","eu")
        if not (is_explicit or is_profile or is_label):
            continue
        x1,y1,x2,y2=b
        cy=(y1+y2)//2
        if cy < height*.72:
            continue
        if (x2-x1) > 0.55*max((bounds(n)[2] for n in nodes if bounds(n)),default=1):
            continue
        score=(100 if is_explicit else 40 if is_profile else 20)
        score+=10 if node.get("clickable")=="true" else 0
        score+=5 if cy>=height*.85 else 0
        candidates.append((score,(x1+x2)//2,cy))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1],candidates[0][2]


def main(argv):
    if len(argv) != 3:
        return 2
    action, filename = argv[1:]
    if action not in {"email-form", "native-chooser", "email-entry", "google-entry", "profile-tab"}:
        return 2
    try:
        xml_text=Path(filename).read_text(encoding="utf-8")
        nodes = parse(xml_text)
    except (OSError, UnicodeError, ET.ParseError):
        return 2
    if action == "email-form":
        return 0 if email_form_visible(nodes) else 1
    if action == "native-chooser":
        return 0 if native_chooser_visible(nodes,xml_text) else 1
    coords = {"email-entry": email_entry, "google-entry": google_entry, "profile-tab": profile_tab}[action](nodes,xml_text)
    if coords is None:
        return 1
    print(*coords)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
