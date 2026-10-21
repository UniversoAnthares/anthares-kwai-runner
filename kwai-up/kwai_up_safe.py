#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
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

# A dedicated physical executor may carry either the full Kwai app or Kwai
# Lite. The rest of the publisher remains fail-closed until the UI contract
# for that exact package has been validated.
CONFIGURED_PACKAGE = os.getenv("KWAI_UP_PACKAGE", "").strip()
if CONFIGURED_PACKAGE:
    if not re.fullmatch(r"[A-Za-z0-9_.]+", CONFIGURED_PACKAGE):
        raise SystemExit("KWAI_UP_STATE=FAILED_SAFE REASON=invalid-package")
    ku.PACKAGE = CONFIGURED_PACKAGE

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
    r"(?:\blog\s*in\b|\bsign\s*in\b|\bentrar\s+(?:na\s+conta|com\s+(?:telefone|google|facebook)|para\s+continuar)\b|\bsenha\b|\bpassword\b|"
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

    def verify_identity(self, *, force_stop: bool = False) -> int:
        expected = self.expected_account()
        pattern = account_pattern(expected)
        home = self.cold_start("05-auth-home", force_stop=force_stop)
        tab = self.profile_tab(home)
        if tab is None:
            raise ku.KwaiUpError("auth-profile-tab-missing")
        self.tap_node(tab)
        deadline = time.time() + 40
        last_blob = ""
        attempts = 0
        recovered_account_chooser = False
        while time.time() < deadline:
            nodes = self.dismiss_known_overlays(self.dump("06-auth-profile"), "06-auth-profile")
            last_blob = ku.text_blob(nodes)
            if pattern.search(last_blob.casefold()):
                self.emit("AUTHENTICATED_IDENTITY", account=expected.lstrip("@"))
                return 0
            if AUTH_REQUIRED_RE.search(last_blob):
                # One safe retry of the already linked account chooser.
                # This does not supply credentials or bypass a login challenge.
                chooser = "trocar de conta" in last_blob.casefold() and "login/cadastre-se" in last_blob.casefold()
                expected_label = expected.lstrip("@").casefold()
                account_label = expected_label in last_blob.casefold() or "lucas rosalem" in last_blob.casefold()
                sign_in = ku.find_text(nodes, ("Entrar",))
                if chooser and account_label and sign_in and not recovered_account_chooser:
                    recovered_account_chooser = True
                    self.tap_node(sign_in, 1)
                    time.sleep(3)
                    continue
                raise ku.KwaiUpError("auth-required")
            if pattern.search(last_blob.casefold()):
                self.emit("AUTHENTICATED_IDENTITY", account=expected.lstrip("@"))
                return 0
            # The Kwai feed intermittently ignores the first tap on Profile.
            # Retry the *same* known tab when the UI proves we are still
            # on the home feed; never infer account identity from a timeout.
            attempts += 1
            # Profile scrolling hides @handle; bring its header back before
            # concluding the session is unauthenticated. Never force-stop app.
            if attempts % 2 == 0 and "editar perfil" in last_blob.casefold():
                for _ in range(3):
                    self.adb.run("shell","input","swipe","330","410","330","1090","230",check=False)
                time.sleep(1)
            if attempts % 2 == 0:
                next_tab = self.profile_tab(nodes)
                if next_tab is not None:
                    self.tap_node(next_tab, 1)
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
            # Second guard before irreversible Android publishing.
            try:
                today = __import__("datetime").datetime.now().astimezone().date().isoformat()
                floor_path = pathlib.Path(__file__).resolve().parents[1] / ".state" / "kwai-daily-cap-owner-confirmed.json"
                floor = 0
                if floor_path.exists():
                    quotas = json.loads(floor_path.read_text(encoding="utf-8"))
                    if quotas.get("schema") != "cortes.daily-owner-floor.v1":
                        raise ValueError("invalid_floor_schema")
                    floor = int(quotas.get("per_target_per_day", {}).get("kwai:lucasrosalem", {}).get(today, 0))
                if floor >= 100:
                    pub.emit("FAILED_SAFE", reason="kwai-daily-limit-100-owner-confirmed")
                    return 72
            except (OSError, ValueError, TypeError):
                pub.emit("FAILED_SAFE", reason="kwai-daily-floor-unreadable")
                return 72
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
