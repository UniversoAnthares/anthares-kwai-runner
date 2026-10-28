#!/usr/bin/env python3
"""Independent Anthares Browser publisher on GitHub-hosted Linux, no Northflank Chromium.

Reads the encrypted Cloudflare browser-state vault, runs isolated headless
Chromium, and reserves each irreversible action in Northflank PostgreSQL.
Fail closed unless signed-in @lucasyahn is proven before touching the ledger.
"""
from __future__ import annotations
import json
import os
import re
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlparse, quote

import requests
from playwright.sync_api import sync_playwright

from tools.x_issue_publisher import fingerprint
from tools.x_publication_safety import _issue_payload, validate_video, verified_post_url

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "infra"))
import anthares_runtime_browser_local as vault

REPO = "UniversoAnthares/anthares-kwai-runner"
GH = "https://api.github.com/repos/" + REPO
LEDGER = "https://http--anthares-ara-northflank--6f6pbqmvhpv6.code.run/x"
ACCOUNT = "lucasyahn"
TRUSTED_MEDIA_HOSTS = {"github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"}


def github(path, method="GET", payload=None):
    token = os.environ["GH_TOKEN"]
    r = requests.request(method, GH + path, json=payload, timeout=32, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
    })
    r.raise_for_status()
    return r.json() if r.content else {}


def _neon_durable(path, payload=None):
    """Cross-runner atomic ledger. Never switch from the old store without reconciliation."""
    from urllib.parse import parse_qs
    if os.getenv("X_LEDGER_MIGRATION_VERIFIED") != "1":
        raise RuntimeError("X_NEON_LEDGER_MIGRATION_NOT_VERIFIED")
    from infra import x_durable_ledger as ledger
    parsed = urlparse(path)
    if parsed.path == "/post-status" and payload is None:
        key = (parse_qs(parsed.query).get("idempotency_key") or [""])[0]
        return {"ok": True, **ledger.readback(key)}
    if parsed.path == "/claim-local" and payload is not None:
        if payload.get("account") != ACCOUNT:
            raise RuntimeError("X_NEON_ACCOUNT_MISMATCH")
        try:
            ledger.begin(payload["idempotency_key"])
        except ledger.AlreadyStarted as exc:
            raise RuntimeError("X_PREVIOUS_SUBMISSION_RECONCILE") from exc
        except ledger.DailyLimitReached as exc:
            raise RuntimeError("X_DAILY_10_LIMIT") from exc
        return {"ok": True, "claimed": True, "account": ACCOUNT}
    if parsed.path == "/confirm-local" and payload is not None:
        if (payload.get("account") != ACCOUNT or
                payload.get("video_verified") is not True or
                payload.get("caption_verified") is not True):
            raise RuntimeError("X_NEON_CONFIRM_EVIDENCE_REQUIRED")
        key = payload["idempotency_key"]
        ledger.confirm(ledger.identity(key), payload["post_url"])
        return {"ok": True, "confirmed": True, "account": ACCOUNT}
    raise RuntimeError("X_NEON_LEDGER_UNSUPPORTED_OPERATION")


def durable(path, payload=None):
    if os.getenv("X_LEDGER_BACKEND") == "neon-api":
        if os.getenv("X_LEDGER_MIGRATION_VERIFIED") != "1":
            raise RuntimeError("X_NEON_LEDGER_NOT_RECONCILED")
        base = os.getenv("X_LEDGER_API", "")
        if base != "https://br-crimson-unit-b89nau08-xledger.compute.c-14.us-east-1.aws.neon.tech/":
            raise RuntimeError("X_NEON_LEDGER_ENDPOINT_MISMATCH")
        operation, mark, query = path.lstrip("/").partition("?")
        if operation not in ("post-status", "claim-local", "confirm-local"):
            raise RuntimeError("X_NEON_LEDGER_INVALID_OPERATION")
        url = base + "?action=" + operation + ("&" + query if mark else "")
        response = requests.request("POST" if payload is not None else "GET", url,
            json=payload, timeout=35,
            headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"]})
        if response.status_code == 409:
            raise RuntimeError("X_PREVIOUS_SUBMISSION_RECONCILE")
        if response.status_code == 429:
            raise RuntimeError("X_DAILY_10_LIMIT")
        if response.status_code != 200:
            raise RuntimeError("X_NEON_LEDGER_HTTP_" + str(response.status_code))
        value = response.json()
        if value.get("ok") is not True:
            raise RuntimeError("X_NEON_LEDGER_REJECTED")
        return value
    if os.getenv("X_LEDGER_BACKEND") == "neon":
        dsn = os.getenv("X_LEDGER_DATABASE_URL", "")
        host = urlparse(dsn).hostname or ""
        if not host.endswith(".neon.tech"):
            raise RuntimeError("X_NEON_DATABASE_URL_REQUIRED")
        return _neon_durable(path, payload)
    if os.getenv("X_CLOUD_PROVIDER") == "codeberg":
        raise RuntimeError("X_CODEBERG_NORTHFLANK_LEDGER_FORBIDDEN")
    shared = os.environ["ARA_SHARED"]
    r = requests.request("POST" if payload is not None else "GET", LEDGER + path,
                         json=payload, timeout=32,
                         headers={"Authorization": "Bearer " + shared})
    if r.status_code == 409:
        raise RuntimeError("X_PREVIOUS_SUBMISSION_RECONCILE")
    if r.status_code == 429:
        raise RuntimeError("X_DAILY_10_LIMIT")
    if r.status_code != 200:
        raise RuntimeError("X_DURABLE_SERVICE_HTTP_" + str(r.status_code))
    value = r.json()
    if value.get("ok") is not True:
        raise RuntimeError("X_DURABLE_LEDGER_DENIED")
    return value


def eligible(issue):
    from tools.x_long_schedule import eligible_time
    if issue.get("state") != "open" or not str(issue.get("title") or "").startswith("[X-PUBLISH]"):
        return None
    p = _issue_payload(issue.get("body") or "")
    if (p.get("platform") != "x" or p.get("account") != ACCOUNT
            or p.get("duration_class") != "long" or p.get("test_fixture")):
        return None
    if not eligible_time(p.get("planned_at")):
        return None
    caption = str(p.get("caption") or "").strip()
    media = urlparse(str(p.get("media_url") or ""))
    if (not 0 < len(caption) <= 280 or media.scheme != "https"
            or media.hostname != "github.com" or media.username or media.password
            or not media.path.startswith("/UniversoAnthares/anthares-kwai-runner/releases/download/")
            or not media.path.endswith(".mp4")
            or not 300 <= float((p.get("microedit") or {}).get("final_duration") or 0) <= 840):
        return None
    return p


def first_item():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    tz = ZoneInfo("America/Campo_Grande")
    # The repository also hosts many unrelated CORTES queues. Query only
    # X publication issues, rather than truncating the generic open-issue list.
    # GitHub Search caps result pagination at 1,000: fail closed on overflow
    # or an incomplete search instead of silently skipping eligible work.
    all_items = []
    query = f'repo:{REPO} is:issue is:open in:title "[X-PUBLISH]"'
    for page in range(1, 11):
        response = requests.get(
            "https://api.github.com/search/issues",
            params={"q": query, "sort": "created", "order": "asc",
                    "per_page": 100, "page": page},
            timeout=32,
            headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"],
                     "Accept": "application/vnd.github+json"},
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or data.get("incomplete_results"):
            raise RuntimeError("X_GITHUB_OPEN_QUEUE_SEARCH_INCOMPLETE")
        total = data.get("total_count")
        batch = data.get("items")
        if (not isinstance(total, int) or total < 0
                or not isinstance(batch, list)):
            raise RuntimeError("X_GITHUB_OPEN_QUEUE_SEARCH_INVALID")
        if total >= 1000:
            raise RuntimeError("X_GITHUB_OPEN_QUEUE_SEARCH_LIMIT")
        all_items.extend(batch)
        if len(all_items) >= total:
            break
        if not batch:
            raise RuntimeError("X_GITHUB_OPEN_QUEUE_SEARCH_INCOMPLETE")
    else:
        raise RuntimeError("X_GITHUB_OPEN_QUEUE_SEARCH_LIMIT")
    ready = []
    for item in all_items:
        if item.get("pull_request"):
            continue
        try:
            p = eligible(item)
            if not p:
                continue
            stamp = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
            if stamp.astimezone(tz).date() > datetime.now(tz).date():
                continue
            ready.append((item, p))
        except (ValueError, TypeError, KeyError):
            continue
    ready.sort(key=lambda pair: (
        0 if pair[1].get("reserve_from") else 1, pair[0]["created_at"], pair[0]["number"]
    ))
    return ready[0] if ready else (None, None)


def account(page):
    if any(s in page.url for s in ("/login", "/i/flow/login", "/i/jf/onboarding")):
        raise RuntimeError("X_CLOUD_SESSION_LOGIN_REQUIRED")
    link = page.locator('a[data-testid="AppTabBar_Profile_Link"]')
    if link.count() and (link.first.get_attribute("href") or "") == "/lucasyahn":
        return
    switcher = page.locator('[data-testid="SideNav_AccountSwitcher_Button"]')
    if switcher.count() != 1:
        raise RuntimeError("X_CLOUD_IDENTITY_NOT_PROVEN")
    matches = re.findall(r"(?<![A-Za-z0-9_])@([A-Za-z0-9_]{1,15})(?![A-Za-z0-9_])",
                         switcher.first.inner_text(timeout=9000))
    if matches != [ACCOUNT]:
        raise RuntimeError("X_CLOUD_WRONG_ACCOUNT")


def proof(context, caption, attempts=1, verified_page=None):
    """Read back X posts on the SAME authenticated tab, never a second tab.

    The full account proof is required before leaving /home and again after
    returning. Failure before submission blocks claim; failure after a click
    leaves started/uncertain fenced in Neon. No pages are created or leaked.
    """
    if verified_page is None or verified_page.context is not context:
        raise RuntimeError("X_CLOUD_INDEPENDENT_IDENTITY_REQUIRED")
    for trial in range(attempts):
        account(verified_page)
        found = None
        try:
            verified_page.goto("https://x.com/lucasyahn",
                               wait_until="domcontentloaded", timeout=50000)
            verified_page.wait_for_timeout(2200)
            dest = urlparse(verified_page.url)
            if (dest.hostname not in ("x.com", "www.x.com")
                    or dest.path.rstrip("/") != "/lucasyahn"):
                raise RuntimeError("X_CLOUD_TIMELINE_PROFILE_MISMATCH")
            for post in verified_page.locator("article").all()[:24]:
                try:
                    if caption not in post.inner_text(timeout=2200):
                        continue
                    for link in post.locator("a").all():
                        href = link.get_attribute("href") or ""
                        match = re.fullmatch(r"/lucasyahn/status/([0-9]+)/?", href)
                        if not match:
                            continue
                        candidate = "https://x.com/lucasyahn/status/" + match.group(1)
                        verified_page.goto(candidate, wait_until="domcontentloaded",
                                           timeout=45000)
                        verified_page.wait_for_timeout(2000)
                        text = " ".join(verified_page.locator(
                            '[data-testid="tweetText"]').all_text_contents())
                        if caption in text and verified_page.locator("video").count() > 0:
                            found = candidate
                        break
                    if found:
                        break
                except Exception:
                    continue
        finally:
            # Restore the same authenticated X tab even when a matching post
            # is absent or a network error interrupted the readback.
            verified_page.goto("https://x.com/home",
                               wait_until="domcontentloaded", timeout=50000)
            deadline = time.monotonic() + 30
            while True:
                try:
                    account(verified_page)
                    break
                except RuntimeError as exc:
                    if str(exc) != "X_CLOUD_IDENTITY_NOT_PROVEN":
                        raise
                    if time.monotonic() >= deadline:
                        raise RuntimeError("X_CLOUD_HOME_IDENTITY_NOT_RESTORED") from None
                    verified_page.wait_for_timeout(1250)
        if found:
            return found
        if trial < attempts - 1:
            verified_page.wait_for_timeout(7500)
    return None

def download(url, dest):
    with requests.get(url, stream=True, allow_redirects=True, timeout=(18, 160)) as r:
        r.raise_for_status()
        parsed = urlparse(r.url)
        if parsed.scheme != "https" or parsed.hostname not in TRUSTED_MEDIA_HOSTS:
            raise RuntimeError("X_UNTRUSTED_MEDIA_REDIRECT")
        count = 0
        with open(dest, "wb") as f:
            for block in r.iter_content(262144):
                count += len(block)
                if count > 99_000_000:
                    raise RuntimeError("X_MEDIA_EXCEEDS_LIMIT")
                f.write(block)
        if count < 100_000:
            raise RuntimeError("X_MEDIA_EMPTY")


def open_authenticated(context):
    page = context.new_page()
    page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=55000)
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            account(page)
            return page
        except RuntimeError as exc:
            if "WRONG_ACCOUNT" in str(exc) or "LOGIN_REQUIRED" in str(exc):
                raise
        page.wait_for_timeout(1250)
    raise RuntimeError("X_CLOUD_ACCOUNT_NOT_PROVEN")


def publish(issue, p, shared_state):
    number = issue["number"]
    key = "x_" + fingerprint(p)
    caption = str(p["caption"]).strip()
    r = durable("/post-status?idempotency_key=" + quote(key, safe=""))
    if r.get("status") != "NOT_FOUND":
        print("X_GH_CLOUD_SKIPPED_PREVIOUS_LEDGER_STATE issue=" + str(number), flush=True)
        return
    comments = github("/issues/" + str(number) + "/comments?per_page=100")
    if len(comments) >= 100:
        raise RuntimeError("X_GH_CLOUD_COMMENTS_PAGINATION")
    if any(any(x in str(c.get("body") or "") for x in
               ("X_SUBMISSION_STARTED_V1", "X_POST_SUBMISSION_STARTED_V1",
                "X_SUBMISSION_UNCERTAIN_V1", "X_LOCAL_SUBMISSION_STARTED_V1"))
           for c in comments):
        raise RuntimeError("X_GH_CLOUD_PREVIOUS_SUBMISSION")
    with TemporaryDirectory(prefix="anthares-x-cloud-") as folder:
        media = Path(folder) / "source.mp4"
        download(p["media_url"], media)
        print("X_GH_CLOUD_PREFLIGHT_MEDIA_DOWNLOADED=PASS", flush=True)
        validate_video(str(media))
        print("X_GH_CLOUD_PREFLIGHT_MEDIA_VERIFIED=PASS", flush=True)
        with sync_playwright() as engine:
            browser = engine.chromium.launch(headless=True, timeout=45000, args=[
                "--no-sandbox", "--disable-dev-shm-usage",
                "--disable-background-networking", "--mute-audio",
            ])
            try:
                context = browser.new_context(storage_state=shared_state, locale="pt-BR",
                                              viewport={"width":1365,"height":768})
                page = open_authenticated(context)
                print("X_GH_CLOUD_PREFLIGHT_ACCOUNT_PROVEN=PASS", flush=True)
                if proof(context, caption, verified_page=page):
                    raise RuntimeError("X_GH_CLOUD_EXISTING_POST_RECONCILE")
                page.goto("https://x.com/compose/post", wait_until="domcontentloaded", timeout=50000)
                account(page)
                dialog = page.locator('[role="dialog"]')
                editor = dialog.locator('[data-testid="tweetTextarea_0"]').first
                editor.wait_for(state="visible", timeout=25000)
                editor.fill(caption)
                dialog.locator('input[type="file"]').last.set_input_files(str(media),timeout=240000)
                button = dialog.locator('[data-testid="tweetButton"]').first
                deadline = time.monotonic() + int(os.getenv("X_CLOUD_MEDIA_WAIT_SECONDS","1700"))
                while time.monotonic() < deadline:
                    account(page)
                    text = "\n".join(dialog.all_inner_texts())
                    if (button.count() == 1 and button.is_enabled()
                            and dialog.locator("video").count() > 0
                            and ("source.mp4: Pronto" in text or "source.mp4: Ready" in text)):
                        break
                    if any(word in text.lower() for word in
                           ("upload failed", "video too long", "vídeo muito longo", "falha no carregamento")):
                        raise RuntimeError("X_GH_CLOUD_UPLOAD_REJECTED")
                    page.wait_for_timeout(5000)
                else:
                    raise RuntimeError("X_GH_CLOUD_MEDIA_TIMEOUT")
                if github("/issues/" + str(number)).get("state") != "open":
                    raise RuntimeError("X_GH_CLOUD_ISSUE_CLOSED")
                account(page)
                durable("/claim-local", {"account": ACCOUNT, "idempotency_key": key})
                github("/issues/" + str(number) + "/comments", "POST",
                       {"body": "X_SUBMISSION_STARTED_V1\nidempotency_key=" + key})
                # Exact same overlay-safe path proven on Windows X videos.
                # PostgreSQL globally fences concurrent local/cloud attempts.
                button.evaluate("""(element, key) => {
                    const sent = window.__antharesCloudSubmissions ||
                                 (window.__antharesCloudSubmissions = new Set());
                    if (sent.has(key)) throw new Error("X_DOUBLE_CLICK_DENIED");
                    if (!element.isConnected || element.getAttribute("aria-disabled")==="true" ||
                        element.disabled) throw new Error("X_POST_BUTTON_NOT_READY");
                    sent.add(key);
                    element.click();
                }""", key, timeout=12000)
                uri = proof(context, caption, attempts=int(os.getenv("X_CLOUD_PROOF_ATTEMPTS","16")), verified_page=page)
                if not uri or verified_post_url(uri) != uri:
                    raise RuntimeError("X_GH_CLOUD_SUBMISSION_UNCERTAIN")
                durable("/confirm-local", {
                    "account": ACCOUNT, "idempotency_key": key,
                    "post_url": uri, "video_verified": True,
                    "caption_verified": True,
                })
                result = {"kind": "X_VIDEO_CONFIRMED_V1", "account": ACCOUNT,
                          "idempotency_key": key, "post_url": uri, "video_verified": True}
                github("/issues/" + str(number) + "/comments", "POST",
                       {"body": "X_VIDEO_CONFIRMED_V1\n" + json.dumps(result, ensure_ascii=False)})
                github("/issues/" + str(number), "PATCH", {"state": "closed"})
                print("X_GH_CLOUD_VIDEO_CONFIRMED=" + uri, flush=True)
            finally:
                browser.close()


def run():
    codeberg = os.getenv("X_CLOUD_PROVIDER") == "codeberg"
    github_runner = (os.getenv("GITHUB_ACTIONS") == "true" and
                     os.getenv("RUNNER_ENVIRONMENT") == "github-hosted")
    forgejo_runner = (os.getenv("FORGEJO_REPOSITORY") == REPO and
                      os.getenv("FORGEJO_REF") == "refs/heads/main" and
                      os.getenv("FORGEJO_SERVER_URL") == "https://codeberg.org")
    if (sys.platform != "linux" or os.getenv("X_CLOUD_ARM") != "1" or
            (not forgejo_runner if codeberg else not github_runner)):
        raise RuntimeError("X_CLOUD_RUNNER_IDENTITY_GUARD")
    if not os.getenv("GH_TOKEN") or not os.getenv("ARA_SHARED"):
        raise RuntimeError("X_GH_CLOUD_CREDENTIAL_MISSING")
    # Every successful cloud run, including idle, must PROVE authenticated
    # account readiness before local standby defers to it.
    state = vault._vault_pull()
    if not state or not isinstance(state.get("cookies"), list):
        raise RuntimeError("X_GH_CLOUD_VAULT_EMPTY")
    issue, data = first_item()
    if not issue:
        with sync_playwright() as engine:
            browser = engine.chromium.launch(headless=True, timeout=45000, args=[
                "--no-sandbox", "--disable-dev-shm-usage", "--mute-audio",
            ])
            try:
                context = browser.new_context(storage_state=state, locale="pt-BR")
                page = open_authenticated(context)
                account(page)
            finally:
                browser.close()
        print("X_GH_CLOUD_AUTHENTICATED_IDLE=lucasyahn", flush=True)
        return
    print("X_GH_CLOUD_ISSUE_PREFLIGHT=" + str(issue["number"]), flush=True)
    publish(issue, data, state)


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        # The Codeberg runner must report specific pre-click safety rejections
        # without printing exception objects, URLs, account cookies or tokens.
        if isinstance(exc, RuntimeError) and re.fullmatch(r"X_[A-Z0-9_]{3,90}", str(exc)):
            print("X_GH_CLOUD_FAILURE_CODE=" + str(exc), flush=True)
        print("X_GH_CLOUD_FAILED=" + type(exc).__name__, flush=True)
        raise SystemExit(2)
