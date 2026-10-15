import json
import sys
import time

import tiktok_web_publish_v2 as v2
from tiktok_session_authority import load_canonical_state

t = v2.t

# The publication process must resolve the same durable session authority used by
# Anthares Browser. Any control-plane/session-file copy is bootstrap material only.
_state, _authority = load_canonical_state()
t.tw.STORAGE_RAW = json.dumps(_state, separators=(",", ":"))
t.tw.STORAGE_FILE = ""
t.tw.EXPECTED_USERNAME = "universo.anthares"
print(
    "TIKTOK_SESSION_AUTHORITY=runtime "
    + "sha256=" + _authority["ciphertext_sha256"]
    + " cookies=" + str(_authority["cookie_count"]),
    flush=True,
)

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
