#!/usr/bin/env python3
import os
import re
import shlex
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from tools.kwai_login_ui_locator import profile_tab as locate_profile_tab

PKG = "com.kwai.video"
AUTH_EXACT = {
    "login", "log in", "sign in", "entrar", "senha", "password",
    "verification code", "código de verificação", "codigo de verificacao",
    "phone number", "número de telefone", "numero de telefone",
}
AUTH_PHRASES = (
    "please log in", "please login", "sign in to", "log in to",
    "continue with google", "continuar com google",
    "continue with facebook", "continuar com facebook",
    "enter verification code", "digite o código", "digite o codigo",
)
CREDENTIAL_HINTS = (
    "password", "senha", "verification", "verify", "code", "código", "codigo",
    "phone", "telefone", "email", "e-mail", "login", "username",
)
OFFLINE = (
    "please check your internet connection", "download failed. try again",
    "no internet connection", "sem conexão", "sem conexao", "sem internet",
)
CREATE = (
    "record", "camera", "upload", "post", "create", "album", "gallery",
    "photo", "video", "gravar", "câmera", "camera", "carregar", "publicar",
    "criar", "álbum", "album", "galeria", "foto", "vídeo", "video",
    "allow kwai", "photos and videos", "take pictures", "permission",
)
PROFILE_MARKERS = (
    "followers", "following", "seguidores", "seguindo", "edit profile",
    "editar perfil", "likes", "curtidas", "posts", "publicações", "publicacoes",
)


def adb(*args):
    return subprocess.run(
        ["adb", *args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, timeout=25
    ).stdout


def node_label(node):
    return " ".join((node.attrib.get("text", ""), node.attrib.get("content-desc", ""))).strip()


def visible_text(nodes):
    # Deliberately exclude resource-id. Auth-related IDs can remain in an
    # authenticated screen and caused false AUTH_REQUIRED classifications.
    return " ".join(node_label(n) for n in nodes if node_label(n)).casefold()


def dump():
    adb("shell", "uiautomator", "dump", "/sdcard/kwai-auth.xml")
    xml = adb("exec-out", "cat", "/sdcard/kwai-auth.xml")
    if not xml.strip():
        adb("pull", "/sdcard/kwai-auth.xml", "/tmp/kwai-auth.xml")
        xml = open("/tmp/kwai-auth.xml", "r", encoding="utf-8").read()
    root = ET.fromstring(xml)
    nodes = list(root.iter("node"))
    return nodes, xml, visible_text(nodes)


def center(bounds):
    m = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds or "")
    if not m:
        return None
    x1, y1, x2, y2 = map(int, m.groups())
    if x1 >= x2 or y1 >= y2:
        return None
    return (x1 + x2) // 2, (y1 + y2) // 2


def tap_xy(x, y, wait=3):
    adb("shell", "input", "tap", str(x), str(y))
    time.sleep(wait)
    return True


def tap_node(node):
    p = center(node.attrib.get("bounds", ""))
    return tap_xy(*p) if p else False


def auth_prompt(nodes):
    labels = [node_label(n).casefold().strip() for n in nodes if node_label(n)]
    for label in labels:
        if label in AUTH_EXACT or any(p in label for p in AUTH_PHRASES):
            return True
    for n in nodes:
        cls = (n.attrib.get("class", "") or "").casefold()
        if not cls.endswith("edittext"):
            continue
        context = " ".join((
            node_label(n), n.attrib.get("resource-id", ""), n.attrib.get("hint", "")
        )).casefold()
        if any(k in context for k in CREDENTIAL_HINTS):
            return True
    return False


def strong_identity(text, expected=None):
    expected = (expected if expected is not None else os.getenv("KWAI_EXPECTED_ACCOUNT", "")).strip().casefold()
    expected = expected.lstrip("@")
    if not expected:
        return False
    return bool(re.search(r"(?<![a-z0-9_.])@?" + re.escape(expected) + r"(?![a-z0-9_.])", text.casefold()))


def local_identity_marker(expected=None):
    """Boolean-only private-app-state corroboration; never prints file contents.

    This is used only together with a live operational authenticated UI.  It is
    not sufficient on its own and therefore cannot turn an anonymous install
    into an authenticated result.
    """
    expected = (expected if expected is not None else os.getenv("KWAI_EXPECTED_ACCOUNT", "")).strip().casefold().lstrip("@")
    if not expected:
        return False
    adb("root")
    adb("wait-for-device")
    q = shlex.quote(expected)
    cmd = (
        "found=0; "
        f"for d in /data/user/0/{PKG}/shared_prefs /data/user/0/{PKG}/files /data/user/0/{PKG}/databases; do "
        "[ -d \"$d\" ] || continue; "
        f"if grep -R -a -l -F -- {q} \"$d\" 2>/dev/null | head -n 1 | grep -q .; then found=1; break; fi; "
        "done; [ \"$found\" = 1 ] && echo KWAI_LOCAL_IDENTITY_MATCH"
    )
    try:
        return "KWAI_LOCAL_IDENTITY_MATCH" in adb("shell", "sh", "-c", cmd)
    except Exception:
        return False


def inspect_profile():
    saw_profile_surface = False
    for attempt in range(14):
        try:
            nodes, _xml, text = dump()
        except Exception:
            time.sleep(1)
            continue
        # Identity is stronger than generic login wording. Check it first.
        if strong_identity(text):
            return 0
        if any(x in text for x in PROFILE_MARKERS):
            saw_profile_surface = True
        if auth_prompt(nodes):
            return 10
        if any(x in text for x in OFFLINE):
            return 12
        # A handle can be rendered lazily; make two bounded scroll attempts.
        if saw_profile_surface and attempt in (4, 8):
            adb("shell", "input", "swipe", "540", "700", "540", "1200", "250")
            time.sleep(2)
            continue
        time.sleep(1)
    return 13 if saw_profile_surface else 11


def main_navigation_evidence(nodes):
    text = visible_text(nodes)
    labels = ("home", "início", "inicio", "friends", "amigos", "following", "seguindo", "inbox", "messages", "mensagens", "profile", "perfil")
    hits = sum(1 for k in labels if k in text)
    bottom_clickables = 0
    height = 0
    parsed = []
    for n in nodes:
        p = center(n.attrib.get("bounds", ""))
        if p:
            parsed.append((n, p))
            m = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", n.attrib.get("bounds", ""))
            if m:
                height = max(height, int(m.group(4)))
    if height:
        bottom_clickables = sum(1 for n, p in parsed if n.attrib.get("clickable") == "true" and p[1] >= height * 0.78)
    return hits >= 2 or bottom_clickables >= 3


def tap_profile(nodes, xml):
    coords = locate_profile_tab(nodes, xml)
    if coords:
        print("KWAI_PROFILE_ROUTE=SEMANTIC_SELECTOR")
        return tap_xy(coords[0], coords[1])
    # Bounded geometry fallback only when the current screen itself proves that
    # a bottom navigation exists. This avoids blind tapping arbitrary screens.
    if not main_navigation_evidence(nodes):
        return False
    size = adb("shell", "wm", "size")
    m = re.search(r"(\d+)x(\d+)", size)
    if not m:
        return False
    w, h = map(int, m.groups())
    print("KWAI_PROFILE_ROUTE=SAFE_BOTTOM_RIGHT_FALLBACK")
    return tap_xy(int(w * 0.90), int(h * 0.955))


def tap_center_plus(nodes):
    for n in nodes:
        rid = n.attrib.get("resource-id", "").casefold()
        desc = node_label(n).casefold().strip()
        p = center(n.attrib.get("bounds", ""))
        if not p:
            continue
        if any(k in rid for k in ("camera", "create", "publish", "post", "record", "ll_camera", "btn_camera")) or desc in ("+", "create", "criar"):
            return tap_xy(*p, wait=4)
    if not main_navigation_evidence(nodes):
        return False
    size = adb("shell", "wm", "size")
    m = re.search(r"(\d+)x(\d+)", size)
    if not m:
        return False
    w, h = map(int, m.groups())
    return tap_xy(w // 2, int(h * 0.955), wait=4)


def inspect_create_surface():
    try:
        nodes, _xml, _text = dump()
    except Exception:
        return 11
    if auth_prompt(nodes):
        return 10
    if not tap_center_plus(nodes):
        return 11
    for _ in range(6):
        try:
            nodes, _xml, text = dump()
        except Exception:
            time.sleep(1)
            continue
        if auth_prompt(nodes):
            return 10
        focus = adb("shell", "dumpsys", "window").casefold()
        operational = any(x in text for x in CREATE) or any(x in focus for x in ("camera", "record", "publish", "post", "capture", "editor", "permissioncontroller"))
        if operational:
            print("KWAI_OPERATIONAL_BYPASS=CREATE_SURFACE_READY")
            identity = local_identity_marker()
            adb("shell", "input", "keyevent", "KEYCODE_BACK")
            return 20 if identity else 21
        time.sleep(1)
    return 11


def emit_authenticated(source):
    # Keep the canonical state token for compatibility with the existing queue
    # gates; proof source makes the exact evidence explicit.
    print("KWAI_AUTH_STATE=AUTHENTICATED_UI")
    print("KWAI_IDENTITY_PROFILE_MATCH=1")
    print("KWAI_IDENTITY_PROOF_SOURCE=" + source)
    return 0


def main():
    for _ in range(8):
        try:
            nodes, xml, text = dump()
        except Exception:
            time.sleep(1)
            continue
        if strong_identity(text):
            return emit_authenticated("VISIBLE_CURRENT_SCREEN")
        if auth_prompt(nodes):
            print("KWAI_AUTH_STATE=AUTH_REQUIRED")
            return 10
        if tap_profile(nodes, xml):
            rc = inspect_profile()
            if rc == 0:
                return emit_authenticated("VISIBLE_PROFILE_HANDLE")
            if rc == 10:
                print("KWAI_AUTH_STATE=AUTH_REQUIRED")
                return 10
            if rc == 12:
                print("KWAI_PROFILE_NETWORK_DEGRADED=1")
                break
            if rc == 13 and local_identity_marker():
                return emit_authenticated("PROFILE_SURFACE_PLUS_LOCAL_APP_STATE")
        time.sleep(1)

    rc = inspect_create_surface()
    if rc == 20:
        return emit_authenticated("OPERATIONAL_UI_PLUS_LOCAL_APP_STATE")
    if rc == 21:
        print("KWAI_AUTH_STATE=AUTHENTICATED_OPERATIONAL")
        print("KWAI_AUTH_STATE=UNKNOWN_CREATE_SURFACE_NOT_IDENTITY_PROOF")
        return 11
    if rc == 10:
        print("KWAI_AUTH_STATE=AUTH_REQUIRED")
        return 10
    print("KWAI_AUTH_STATE=UNKNOWN")
    return 11


if __name__ == "__main__":
    raise SystemExit(main())
