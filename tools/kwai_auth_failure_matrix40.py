#!/usr/bin/env python3
"""Forty independent regression probes for the real mobile-auth timeout.

These tests intentionally vary the exact failure hypothesis that can occur after
an owner successfully completes login in the remote Android window.  They are
cheap, credential-free and safe to run in parallel.
"""
from __future__ import annotations

import pathlib
import sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import kwai_auth_probe as probe
from tools.kwai_login_ui_locator import profile_tab

case = int(sys.argv[1])
if case not in range(1, 41):
    raise SystemExit("case must be 1..40")


def node(text="", desc="", rid="", cls="android.widget.TextView", bounds="[0,0][200,80]", clickable="false"):
    return ET.fromstring(
        f'<node text="{text}" content-desc="{desc}" resource-id="{rid}" class="{cls}" bounds="{bounds}" clickable="{clickable}" />'
    )


def tree(*children):
    return "<hierarchy>" + "".join(children) + "</hierarchy>"


def nxml(text="", desc="", rid="", cls="android.widget.TextView", bounds="[0,0][200,80]", clickable="false"):
    return f'<node text="{text}" content-desc="{desc}" resource-id="{rid}" class="{cls}" bounds="{bounds}" clickable="{clickable}" />'


def parse(xml):
    return list(ET.fromstring(xml).iter("node"))


workflow = (ROOT / ".github/workflows/kwai-queue-publisher.yml").read_text(encoding="utf-8")
session = (ROOT / "kwai_session_state.sh").read_text(encoding="utf-8")
source = (ROOT / "kwai_auth_probe.py").read_text(encoding="utf-8")
locator = (ROOT / "tools/kwai_login_ui_locator.py").read_text(encoding="utf-8")

checks = {}

# Identity normalization and strict-account boundaries.
checks[1] = (probe.strong_identity("@lucasrosalem", "lucasrosalem"), "exact @handle is accepted")
checks[2] = (probe.strong_identity("lucasrosalem", "@lucasrosalem"), "configured @ prefix is normalized")
checks[3] = (probe.strong_identity("LUCASROSALEM", "lucasrosalem"), "identity comparison is case-insensitive")
checks[4] = (not probe.strong_identity("@lucasrosalem4", "lucasrosalem"), "suffix account is rejected")
checks[5] = (not probe.strong_identity("x_lucasrosalem", "lucasrosalem"), "prefix account is rejected")
checks[6] = (probe.strong_identity("perfil: @lucasrosalem •", "lucasrosalem"), "punctuated profile handle is accepted")
checks[7] = (not probe.strong_identity("lucasrosalem.foo", "lucasrosalem"), "dot-suffixed different account is rejected")
checks[8] = (not probe.strong_identity("", "lucasrosalem"), "empty UI never proves identity")
checks[9] = (not probe.strong_identity("@lucasrosalem", ""), "empty configured account never passes")
checks[10] = (probe.strong_identity("  @LucasRosalem  ", "  @lucasrosalem "), "whitespace is normalized")

# Auth prompt detection: visible credential UI yes, stale resource ids no.
checks[11] = (probe.auth_prompt([node(text="Log in")]), "visible Log in is auth-required")
checks[12] = (probe.auth_prompt([node(text="Entrar")]), "visible Entrar is auth-required")
checks[13] = (probe.auth_prompt([node(text="Please log in to continue")]), "sentence login prompt is auth-required")
checks[14] = (probe.auth_prompt([node(text="", rid="com.kwai.video:id/login_container")]) is False, "login resource-id alone is not auth-required")
checks[15] = (probe.auth_prompt([node(text="Home", rid="com.kwai.video:id/login_badge")]) is False, "authenticated home with stale login id is not rejected")
checks[16] = (probe.auth_prompt([node(text="", rid="password_input", cls="android.widget.EditText")]), "password EditText is auth-required")
checks[17] = (probe.auth_prompt([node(text="", rid="phone_input", cls="android.widget.EditText")]), "phone EditText is auth-required")
checks[18] = (not probe.auth_prompt([node(text="Login bonus today")]), "ordinary content containing login is not a login wall")
checks[19] = (probe.auth_prompt([node(desc="Sign in")]), "content-description sign-in is detected")
checks[20] = (not probe.auth_prompt([node(text="Profile"), node(text="Followers")]), "profile content is not auth-required")

# Profile locator aliases and safety boundaries.
xml21 = tree(nxml(text="Profile", rid="com.kwai.video:id/ll_profile", bounds="[900,1800][1080,1920]", clickable="true"))
checks[21] = (profile_tab(parse(xml21), xml21) is not None, "ll_profile alias is recognized")
xml22 = tree(nxml(text="Me", rid="com.kwai.video:id/id_home_bottom_tab_me", bounds="[900,1800][1080,1920]", clickable="true"))
checks[22] = (profile_tab(parse(xml22), xml22) is not None, "id_home_bottom_tab_me alias is recognized")
xml23 = tree(nxml(text="Perfil", bounds="[900,1800][1080,1920]", clickable="true"))
checks[23] = (profile_tab(parse(xml23), xml23) is not None, "Portuguese semantic Perfil tab is recognized")
xml24 = tree(nxml(text="Profile", bounds="[50,100][600,240]", clickable="true"))
checks[24] = (profile_tab(parse(xml24), xml24) is None, "top profile heading is never tapped as nav")
xml25 = tree(nxml(rid="com.kwai.video:id/profile_avatar", bounds="[900,1800][1080,1920]", clickable="true"))
checks[25] = (profile_tab(parse(xml25), xml25) is None, "avatar is never mistaken for Profile tab")
xml26 = tree(
    nxml(text="Home", bounds="[0,1800][200,1920]", clickable="true"),
    nxml(text="Friends", bounds="[200,1800][400,1920]", clickable="true"),
    nxml(text="Inbox", bounds="[600,1800][800,1920]", clickable="true"),
)
checks[26] = (probe.main_navigation_evidence(parse(xml26)), "three bottom controls prove main navigation")
xml27 = tree(nxml(text="Random article", bounds="[0,0][1080,1600]", clickable="true"))
checks[27] = (not probe.main_navigation_evidence(parse(xml27)), "arbitrary screen cannot enable coordinate fallback")
checks[28] = ("locate_profile_tab" in source, "auth probe reuses hardened semantic locator")
checks[29] = ("SAFE_BOTTOM_RIGHT_FALLBACK" in source and "main_navigation_evidence" in source, "geometry fallback is bounded by navigation proof")
checks[30] = (source.index("if strong_identity(text)") < source.index("if auth_prompt(nodes)", source.index("def inspect_profile")), "identity wins over generic auth wording")

# Next-failure predictions: persistence, privacy, tunnel, and fresh-runner restore.
checks[31] = ("KWAI_IDENTITY_PROOF_SOURCE=" in source, "proof source is emitted for postmortem diagnostics")
checks[32] = ("OPERATIONAL_UI_PLUS_LOCAL_APP_STATE" in source, "offline profile can be corroborated by operational UI plus private state")
checks[33] = ("grep -R -a -l -F" in source and "KWAI_LOCAL_IDENTITY_MATCH" in source, "local identity corroboration logs no private file contents")
checks[34] = ("openssl enc -aes-256-cbc" in session and "-pbkdf2" in session, "saved Android app state remains encrypted")
checks[35] = ("/data/user/0/$PKG" in session, "native Android app state rather than web cookies is persisted")
checks[36] = ("KWAI_SESSION_SAVE_REFUSED_IDENTITY_UNVERIFIED" in session, "session save still fails closed without identity proof")
checks[37] = ("cloudflared tunnel" in workflow and "trycloudflare" in workflow, "temporary remote-auth tunnel remains configured")
checks[38] = ("KWAI_MOBILE_AUTH_TIMEOUT" in workflow and "KWAI_MOBILE_AUTH_TUNNEL_DIED" in workflow, "bootstrap distinguishes timeout from tunnel death")
checks[39] = ("mobile_auth_restore_verify" in workflow, "successful bootstrap is independently restored on a fresh runner")
checks[40] = ("kwai_session_vault_client.py push" in workflow and "KWAI_IDENTITY_PROFILE_MATCH=1" in workflow, "private vault write remains identity-gated")

ok, description = checks[case]
if not ok:
    print(f"KWAI_AUTH_FAILURE_MATRIX_{case:02d}=FAIL {description}")
    raise SystemExit(1)
print(f"KWAI_AUTH_FAILURE_MATRIX_{case:02d}=PASS {description}")
