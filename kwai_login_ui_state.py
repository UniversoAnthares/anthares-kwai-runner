#!/usr/bin/env python3
"""Classify Kwai Android UIAutomator login screens without logging user data."""
import re
import sys
import xml.etree.ElementTree as ET


def classify(xml_text):
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return "UNKNOWN"
    nodes = list(root.iter("node"))
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
    ):
        return "CHOOSER"
    return "UNKNOWN"


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: kwai_login_ui_state.py UI_XML_PATH")
    try:
        with open(sys.argv[1], "r", encoding="utf-8") as stream:
            data = stream.read()
    except OSError:
        print("UNKNOWN")
        return
    print(classify(data))


if __name__ == "__main__":
    main()
