#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import pathlib
import re
import sys
import time

CORE = pathlib.Path(__file__).with_name("kwai_up.py")
SPEC = importlib.util.spec_from_file_location("kwai_up_core", CORE)
if SPEC is None or SPEC.loader is None:
    raise SystemExit("KWAI_UP_STATE=FAILED_SAFE REASON=core-load-failed")
ku = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ku
SPEC.loader.exec_module(ku)

# Preserve the semantics that were learned by the successful 2026-10-02
# publisher: a review/pending message is not publication proof.
ku.SUCCESS_RE = re.compile(
    r"(?:publicado\s+com\s+sucesso|publicado\s+con\s+[ée]xito|"
    r"enviado\s+com\s+sucesso(?!\s*,?\s*por\s+favor\s+aguarde\s+a\s+revis[aã]o)|"
    r"v[ií]deo\s+publicado\b|\bpublished\b|\bposted\b)",
    re.I,
)
ku.FAILURE_RE = re.compile(
    r"(?:voc[eê]\s+ainda\s+n[aã]o\s+publicou\s+nada|"
    r"este\s+usu[aá]rio\s+ainda\s+n[aã]o\s+publicou\s+nenhum\s+v[ií]deo|"
    r"no\s+has\s+publicado|a[uú]n\s+no\s+public[oó]|"
    r"est[áa]\s+sendo\s+publicado|tente\s+novamente(?:\s+mais\s+tarde)?|try\s+again|"
    r"enviado\s+com\s+sucesso\s*,?\s*por\s+favor\s+aguarde\s+a\s+revis[aã]o|"
    r"falhou|failed|\berro\b|\berror\b|upload\s+failed)",
    re.I,
)

AUTH_REQUIRED_RE = re.compile(
    r"(?:\blog\s*in\b|\bsign\s*in\b|\bentrar\b|\bsenha\b|\bpassword\b|"
    r"c[oó]digo\s+de\s+verifica[cç][aã]o|verification\s+code|"
    r"n[uú]mero\s+de\s+telefone|phone\s+number|continue\s+with\s+google|"
    r"continuar\s+com\s+google|continue\s+with\s+facebook|continuar\s+com\s+facebook)",
    re.I,
)


def account_pattern(account: str) -> re.Pattern[str]:
    account = account.strip().casefold().lstrip("@")
    if not account:
        raise ku.KwaiUpError("KWAI_UP_EXPECTED_ACCOUNT-missing")
    return re.compile(r"(?<![a-z0-9_.])@?" + re.escape(account) + r"(?![a-z0-9_.])", re.I)


class SafePublisher(ku.Publisher):
    def expected_account(self) -> str:
        value = os.getenv("KWAI_UP_EXPECTED_ACCOUNT", "").strip()
        if not value:
            raise ku.KwaiUpError("KWAI_UP_EXPECTED_ACCOUNT-missing")
        return value

    def verify_identity(self) -> int:
        expected = self.expected_account()
        pattern = account_pattern(expected)
        home = self.cold_start("05-auth-home")
        tab = self.profile_tab(home)
        if tab is None:
            raise ku.KwaiUpError("auth-profile-tab-missing")
        self.tap_node(tab)
        deadline = time.time() + 40
        last_blob = ""
        while time.time() < deadline:
            nodes = self.dismiss_known_overlays(self.dump("06-auth-profile"), "06-auth-profile")
            last_blob = ku.text_blob(nodes)
            if AUTH_REQUIRED_RE.search(last_blob):
                raise ku.KwaiUpError("auth-required")
            if pattern.search(last_blob.casefold()):
                self.emit("AUTHENTICATED_IDENTITY", account=expected.lstrip("@"))
                return 0
            time.sleep(2)
        raise ku.KwaiUpError("authenticated-identity-unverified")

    def prepare(self) -> int:
        if self.probe() != 0:
            return 20
        self.verify_identity()
        # Base prepare rechecks transport/package before the irreversible path.
        return super().prepare()


def main() -> int:
    mode = (sys.argv[1] if len(sys.argv) > 1 else "probe").strip().lower()
    if mode not in {"probe", "auth", "prepare", "commit", "verify"}:
        print("KWAI_UP_STATE=FAILED_SAFE REASON=invalid-mode", flush=True)
        return 64
    cfg = ku.Config.from_env("probe" if mode == "auth" else mode)
    pub = SafePublisher(cfg)
    try:
        if mode == "probe":
            return pub.probe()
        if mode == "auth":
            if pub.probe() != 0:
                return 20
            return pub.verify_identity()
        if mode == "prepare":
            return pub.prepare()
        if mode == "commit":
            return pub.commit()
        return pub.verify()
    except ku.HumanVerification as exc:
        pub.emit("FAILED_SAFE", reason="human-verification", detail=ku.safe_token(str(exc)))
        return 91
    except ku.KwaiUpError as exc:
        pub.emit("FAILED_SAFE", reason=ku.safe_token(str(exc), "kwai-up-error"))
        return 70
    except Exception as exc:
        pub.emit("FAILED_SAFE", reason="unexpected", detail=ku.safe_token(type(exc).__name__))
        return 79


if __name__ == "__main__":
    raise SystemExit(main())
