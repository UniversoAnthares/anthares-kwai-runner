import re
import sys
import time

import tiktok_web_publish as t


def dismiss_known_dialog(page):
    labels = ("Ativar", "Enable", "Entendi", "Got it", "OK")
    for label in labels:
        try:
            loc = page.get_by_role("button", name=label, exact=True)
            if loc.first.is_visible(timeout=700):
                loc.first.click(timeout=8000)
                time.sleep(2)
                return True
        except Exception:
            pass
    return False


def set_public(page):
    text = t.page_text(page, 22000)
    if re.search(r"\b(Todos|Everyone|Público|Public)\b", text, re.I):
        return True

    for current in ("Seguidores", "Followers", "Amigos", "Friends", "Somente você", "Apenas você", "Only you"):
        try:
            loc = page.get_by_text(current, exact=True)
            if loc.first.is_visible(timeout=700):
                loc.first.click(timeout=8000)
                time.sleep(1)
                break
        except Exception:
            pass

    for target in ("Todos", "Everyone", "Público", "Public"):
        try:
            loc = page.get_by_text(target, exact=True)
            if loc.first.is_visible(timeout=900):
                loc.first.click(timeout=8000)
                time.sleep(1)
                return True
        except Exception:
            pass

    text = t.page_text(page, 22000)
    if re.search(r"Seguidores|Followers|Somente você|Apenas você|Only you|Amigos|Friends", text, re.I):
        return False
    return None


_original_wait = t.wait_upload_ready


def wait_ready(page, timeout_seconds=360):
    button = _original_wait(page, timeout_seconds)
    for _ in range(4):
        if not dismiss_known_dialog(page):
            break
    return t.enabled_post_button(page) or button


t.handle_auto_checks_modal = dismiss_known_dialog
t.set_public_visibility = set_public
t.privacy_is_public_or_selectable = set_public
t.wait_upload_ready = wait_ready

if __name__ == "__main__":
    print("Anthares TikTok Web Publisher v2", flush=True)
    try:
        t.main()
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr, flush=True)
        raise
