#!/usr/bin/env python3
"""Thirty independent, cheap contract probes for phone-only Kwai authentication."""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
case = int(sys.argv[1])
if not 1 <= case <= 30:
    raise SystemExit("case must be 1..30")

workflow = (ROOT / ".github/workflows/kwai-queue-publisher.yml").read_text(encoding="utf-8")
headless = (ROOT / "kwai_headless_login.sh").read_text(encoding="utf-8")
session = (ROOT / "kwai_session_state.sh").read_text(encoding="utf-8")
vault = (ROOT / "tools/kwai_session_vault_client.py").read_text(encoding="utf-8")
publish_runtime = (ROOT / "kwai_queue_publish_runtime.sh").read_text(encoding="utf-8")

bootstrap = re.search(r"mobile_auth_bootstrap:.*?mobile_auth_restore_verify:", workflow, re.S)
bootstrap_text = bootstrap.group(0) if bootstrap else ""

checks = {
    1: ("KWAI_AUTH_STRATEGY:-mobile_only" in headless, "mobile_only is the default auth strategy"),
    2: ("KWAI_CREDENTIAL_FALLBACK_DISABLED" in headless, "credential fallback is explicitly disabled"),
    3: ("KWAI_MOBILE_REAUTH_REQUIRED" in headless, "expired sessions request mobile reauth"),
    4: (headless.find("kwai_session_state.sh restore") < headless.find("kwai_auth_probe.py"), "session restore precedes identity probe"),
    5: ("credential_fallback" in headless, "legacy credentials require explicit opt-in"),
    6: ("openssl enc -aes-256-cbc" in session, "saved session is encrypted"),
    7: ("openssl enc -d -aes-256-cbc" in session, "restored session is decrypted locally"),
    8: ("KWAI_SESSION_SAVE_REFUSED_IDENTITY_UNVERIFIED" in session, "session save requires verified identity"),
    9: ("KWAI_IDENTITY_PROFILE_MATCH=1" in session, "session save pins the expected account"),
    10: ("/data/user/0/$PKG" in session, "Android app state is persisted rather than web cookies"),
    11: ("/kwai/session-vault" in vault, "private Cloudflare session vault remains canonical"),
    12: ("Authorization" in vault and "Bearer" in vault, "vault client uses authenticated requests"),
    13: ("KWAI_SESSION_FILE: kwai-session.enc" in workflow, "workflow uses encrypted session file"),
    14: ("mobile_auth" in workflow, "publisher workflow exposes mobile-auth bootstrap mode"),
    15: ("mobile_auth_bootstrap" in workflow, "workflow contains remote auth bootstrap job"),
    16: ("mobile_auth_contract_matrix" in workflow, "workflow contains 30-way auth contract matrix"),
    17: ("max-parallel: 30" in workflow, "auth contract tests can run thirty-way in parallel"),
    18: ("kwai-mobile-auth-access" in workflow, "remote auth access is isolated in a temporary artifact"),
    19: ("retention-days: 1" in workflow, "auth access artifact has short retention"),
    20: ("::add-mask::" in workflow, "temporary GUI password is masked from logs"),
    21: ("htpasswd" in workflow and "auth_basic" in workflow, "remote GUI is protected by HTTP basic auth"),
    22: ("trycloudflare.com" in workflow, "auth window uses a temporary Cloudflare tunnel"),
    23: ("kwai_auth_probe.py" in workflow, "remote login completion uses real account UI proof"),
    24: ("kwai_session_state.sh save" in workflow, "successful mobile login is sealed for reuse"),
    25: ("kwai_session_vault_client.py push" in workflow, "sealed session is pushed to private vault"),
    26: ("mobile_auth_restore_verify" in workflow, "fresh-runner restore is independently verified"),
    27: ("KWAI_AUTH_STRATEGY: mobile_only" in workflow, "publisher runtime is pinned to mobile-only auth"),
    28: (bool(bootstrap_text) and "KWAI_LOGIN" not in bootstrap_text, "mobile bootstrap never consumes login credentials"),
    29: ("bash kwai_run_next_job.sh" in publish_runtime, "canonical queue runtime remains the publication boundary"),
    30: (bool(bootstrap_text) and "MEmu" not in bootstrap_text and "self-hosted" not in bootstrap_text, "mobile auth bootstrap has no PC/MEmu executor dependency"),
}

ok, description = checks[case]
if not ok:
    print(f"MOBILE_AUTH_CONTRACT_{case:02d}=FAIL {description}")
    raise SystemExit(1)
print(f"MOBILE_AUTH_CONTRACT_{case:02d}=PASS {description}")
