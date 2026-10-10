#!/usr/bin/env python3
"""Classify Kwai Android login UI and choose a safe non-Google login target.

Only screen state and Android tap coordinates leave this process. No account
identifiers, field values, credentials, or XML content are logged.
"""
import re
import sys
import xml.etree.ElementTree as ET


def parse_nodes(xml_text):
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    return list(root.iter("node"))


def classify(xml_text):
    nodes = parse_nodes(xml_text)
    labels = " ".join(
        " ".join((node.get("text", ""), node.get("content-desc", ""),
                  node.get("resource-id", "")))
        for node in nodes
    ).casefold()
    fields = [node for node in nodes
              if node.get("class", "").endswith("EditText")]
    if fields and re.search(
        r"password|senha|e-?mail|phone|telefone|verification|verifica|"
        r"login|log in|sign in|entrar|code|código|continue|continuar", labels
    ):
        return "CREDENTIAL_FORM"
    if "login_platform_expand_text" in labels or (
        "create your profile" in labels and "continue with google" in labels
    ) or ("continue with google" in labels and re.search(
        r"phone|telefone|e-?mail", labels
    )):
        return "CHOOSER"
    return "UNKNOWN"


def target_coordinates(xml_text):
    """Select Email, Phone, or the chooser expander; never select Google.

    A valid Android bounds rectangle is mandatory. Fail closed if there is no
    semantically supported target. In particular, never tap a blind location.
    """
    if classify(xml_text) != "CHOOSER":
        return None
    candidates = []
    for node in parse_nodes(xml_text):
        label = " ".join((node.get("text", ""), node.get("content-desc", ""))).strip().casefold()
        rid = node.get("resource-id", "").casefold()
        bounds = re.fullmatch(
            r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.get("bounds", "")
        )
        if not bounds:
            continue
        x1, y1, x2, y2 = map(int, bounds.groups())
        if x2 <= x1 or y2 <= y1:
            continue
        if re.fullmatch(r"(e-?mail|email address|endereço de e-mail)", label):
            rank, action = 0, "EMAIL"
        elif re.fullmatch(r"(phone|telefone|phone number|número de telefone)", label):
            rank, action = 1, "PHONE"
        elif "login_platform_expand_text" in rid and re.search(
            r"phone|telefone|e-?mail", label
        ):
            rank, action = 2, "EXPAND"
        elif re.fullmatch(r"(other methods|other ways|more options|outras opções|outras formas)", label):
            rank, action = 3, "MORE"
        else:
            continue
        candidates.append((rank, action, (x1 + x2) // 2, (y1 + y2) // 2))
    if not candidates:
        return None
    _, action, x, y = min(candidates)
    return action, x, y


def main():
    if len(sys.argv) not in (2, 3) or (len(sys.argv) == 3 and sys.argv[2] != "--target"):
        raise SystemExit("usage: kwai_login_ui_state.py UI_XML_PATH [--target]")
    try:
        with open(sys.argv[1], "r", encoding="utf-8") as stream:
            data = stream.read()
    except OSError:
        data = ""
    if len(sys.argv) == 2:
        print(classify(data))
        return
    target = target_coordinates(data)
    if target is None:
        raise SystemExit(1)
    action, x, y = target
    print(action, x, y)


if __name__ == "__main__":
    main()
