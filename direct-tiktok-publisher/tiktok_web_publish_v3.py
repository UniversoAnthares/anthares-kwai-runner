import json
import os
import sys
import time

import tiktok_web_publish_v2 as v2
from tiktok_session_authority import load_canonical_state

t = v2.t

# The Codeberg primary receives an isolated session file only AFTER the hosted
# controller has verified the exact account in TikTok's live profile. The local
# Anthares Browser vault, which needs ARA_SHARED, is not available there.
if os.getenv("FORGEJO_REPOSITORY") == "UniversoAnthares/anthares-kwai-runner":
    expected = os.getenv("EXPECTED_TIKTOK_USERNAME", "").strip().lstrip("@").lower()
    if expected != "universo.anthares" or not os.getenv("TIKTOK_STORAGE_STATE_FILE"):
        raise RuntimeError("TIKTOK_CODEBERG_VERIFIED_ACCOUNT_STATE_REQUIRED")
    _state = t.tw.storage_state()
    if not t.tw.auth_cookie_names(_state):
        raise RuntimeError("TIKTOK_CODEBERG_AUTH_COOKIES_REQUIRED")
    print("TIKTOK_SESSION_AUTHORITY=codeberg-dedicated cookies="
          + str(len(_state["cookies"])), flush=True)
else:
    # Preserve the original durable Anthares Browser authority for local and
    # non-Codeberg executions. No silent fallback to unverified cookies.
    _state, _authority = load_canonical_state()
    print(
        "TIKTOK_SESSION_AUTHORITY=runtime "
        + "sha256=" + _authority["ciphertext_sha256"]
        + " cookies=" + str(_authority["cookie_count"]),
        flush=True,
    )

t.tw.STORAGE_RAW = json.dumps(_state, separators=(",", ":"))
t.tw.STORAGE_FILE = ""
t.tw.EXPECTED_USERNAME = "universo.anthares"

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
