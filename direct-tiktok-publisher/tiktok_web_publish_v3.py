import sys
import time

import tiktok_web_publish_v2 as v2

t = v2.t
_original_wait_confirmation = t.wait_confirmation


def wait_confirmation(page, previous_url, timeout_seconds=90):
    for label in ("Publicar agora", "Publish now", "Continuar publicando", "Continue posting"):
        try:
            button = page.get_by_role("button", name=label, exact=False).first
            if button.is_visible(timeout=900):
                button.click(timeout=10000)
                time.sleep(2)
                break
        except Exception:
            pass
    return _original_wait_confirmation(page, previous_url, timeout_seconds)


t.wait_confirmation = wait_confirmation

if __name__ == "__main__":
    print("Anthares TikTok Web Publisher v3", flush=True)
    try:
        t.main()
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr, flush=True)
        raise
