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
    """Confirm the selected privacy control, never page-wide text.

    Seeing the word 'Public' in a Post button or hidden menu is insufficient.
    A restricted selection must be changed and then checked again.
    """
    public = ("Todos", "Everyone", "Público", "Public")
    restricted = ("Somente você", "Apenas você", "Only you",
                  "Amigos", "Friends", "Seguidores", "Followers")

    def visible(label):
        try:
            node=page.get_by_text(label,exact=True).first
            return node if node.is_visible(timeout=650) else None
        except Exception:
            return None

    active_restricted=next((node for label in restricted if (node:=visible(label))),None)
    if active_restricted is not None:
        active_restricted.click(timeout=8000)
        time.sleep(1)
        option=None
        for label in public:
            try:
                item=page.get_by_role("option",name=label,exact=True).first
                if item.is_visible(timeout=650):
                    option=item
                    break
            except Exception:
                pass
            option=visible(label)
            if option is not None:break
        if option is None:return False
        option.click(timeout=8000)
        time.sleep(1)

    # Exact, visible selected text is required. Reject ambiguous mixed states.
    is_public=any(visible(label) is not None for label in public)
    is_restricted=any(visible(label) is not None for label in restricted)
    return True if is_public and not is_restricted else False

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
