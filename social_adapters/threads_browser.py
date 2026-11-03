#!/usr/bin/env python3
"""Browser UI publisher for a personal Threads account.

Uses an ordinary authenticated Threads web session. A submission is only
reported as CONFIRMED after a new public /@account/post/<code> permalink is
observed on the expected profile.
"""
import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit


class BrowserPublishError(RuntimeError):
    pass


class AuthenticationRequired(BrowserPublishError):
    pass


class IdentityMismatch(BrowserPublishError):
    pass


class PublicationUnverified(BrowserPublishError):
    pass


def normalize_account(value):
    return str(value or "").strip().lstrip("@").casefold()


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_post_url(account, href):
    if not href:
        return ""
    if href.startswith("/"):
        href = urljoin("https://www.threads.com", href)
    parsed = urlsplit(href)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or host not in {
        "threads.com", "www.threads.com", "threads.net", "www.threads.net"
    }:
        return ""
    match = re.search(r"/@([^/]+)/post/([A-Za-z0-9_-]+)", parsed.path)
    if not match:
        return ""
    expected = normalize_account(account)
    observed = normalize_account(match.group(1))
    if observed != expected:
        return ""
    return f"https://www.threads.com/@{expected}/post/{match.group(2)}"


def external_id_from_url(url):
    match = re.search(r"/post/([A-Za-z0-9_-]+)", urlsplit(url).path)
    return match.group(1) if match else ""


def _first_visible(locators, timeout_ms=1400):
    for locator in locators:
        try:
            locator.first.wait_for(state="visible", timeout=timeout_ms)
            return locator.first
        except Exception:
            continue
    return None


def _body_text(page):
    try:
        return page.locator("body").inner_text(timeout=3000) or ""
    except Exception:
        return ""


def _auth_wall(page):
    url = page.url.lower()
    if "/login" in url or "/accounts/login" in url:
        return True
    text = _body_text(page).casefold()
    needles = (
        "log in with instagram", "log in to threads", "entrar com o instagram",
        "entrar no threads", "verify your identity", "confirme sua identidade",
    )
    return any(n in text for n in needles)


def _profile_url(account):
    return f"https://www.threads.com/@{normalize_account(account)}"


def _ensure_expected_account(page, account):
    page.goto(_profile_url(account), wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1500)
    if _auth_wall(page):
        raise AuthenticationRequired("threads: login/session challenge detected")
    own = _first_visible([
        page.get_by_role("button", name=re.compile(r"Edit profile|Editar perfil", re.I)),
        page.get_by_role("link", name=re.compile(r"Edit profile|Editar perfil", re.I)),
    ], timeout_ms=2200)
    if own is None:
        raise IdentityMismatch(
            f"threads: expected account @{normalize_account(account)} is not verified as signed-in owner"
        )


def _latest_post_url(page, account):
    page.goto(_profile_url(account), wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1400)
    if _auth_wall(page):
        raise AuthenticationRequired("threads: authentication required while checking profile")
    links = page.locator('a[href*="/post/"]')
    for i in range(min(links.count(), 50)):
        url = canonical_post_url(account, links.nth(i).get_attribute("href") or "")
        if url:
            return url
    return ""


def _publish_threads(page, video, caption):
    intent = "https://www.threads.com/intent/post?text=" + quote(caption or "")
    page.goto(intent, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1600)
    if _auth_wall(page):
        raise AuthenticationRequired("threads: composer requires authentication")

    editor = _first_visible([
        page.locator('[contenteditable="true"][role="textbox"]'),
        page.locator('[contenteditable="true"]'),
        page.get_by_role("textbox"),
    ], timeout_ms=3000)
    if editor is None:
        raise BrowserPublishError("threads: composer editor not found")

    # The intent should prefill text. Fill explicitly if it did not.
    if caption:
        try:
            current = (editor.inner_text(timeout=1500) or "").strip()
        except Exception:
            current = ""
        if caption.strip() not in current:
            editor.fill(caption)

    file_input = page.locator('input[type="file"]').first
    try:
        file_input.wait_for(state="attached", timeout=5000)
    except Exception as exc:
        raise BrowserPublishError("threads: media upload input not found") from exc
    file_input.set_input_files(str(video))
    page.wait_for_timeout(2200)

    post = _first_visible([
        page.get_by_role("button", name=re.compile(r"^Post$|^Publicar$|^Postar$", re.I)),
        page.locator('div[role="button"]').filter(has_text=re.compile(r"^Post$|^Publicar$|^Postar$", re.I)),
    ], timeout_ms=3500)
    if post is None:
        raise BrowserPublishError("threads: Post control not found")

    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            if post.is_enabled():
                post.click()
                return
        except Exception:
            pass
        page.wait_for_timeout(850)
    raise BrowserPublishError("threads: Post control never became enabled after media upload")


def _wait_for_new_post(page, account, previous_url, timeout_seconds=120):
    deadline = time.time() + timeout_seconds
    last = ""
    while time.time() < deadline:
        try:
            last = _latest_post_url(page, account)
            if last and last != previous_url:
                remote_id = external_id_from_url(last)
                if remote_id:
                    return {"remote_id": remote_id, "permalink": last}
        except AuthenticationRequired:
            raise
        except Exception:
            pass
        page.wait_for_timeout(2500)
    raise PublicationUnverified(
        f"threads: submit completed but no new public post was independently observed; last={last!r}"
    )


def publish(platform, video, caption, account, profile, commit=False, headless=True):
    if str(platform).casefold() != "threads":
        raise ValueError("unsupported platform")
    video = Path(video).resolve()
    profile = Path(profile).resolve()
    if not video.is_file():
        raise FileNotFoundError(video)
    if not normalize_account(account):
        raise ValueError("account is required")
    summary = {
        "platform": "threads",
        "account": normalize_account(account),
        "video": str(video),
        "content_sha256": file_sha256(video),
    }
    if not commit:
        return {**summary, "status": "DRY_RUN"}

    from playwright.sync_api import sync_playwright

    profile.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(profile), headless=headless, accept_downloads=False,
            viewport={"width": 1280, "height": 900},
        )
        page = context.pages[0] if context.pages else context.new_page()
        try:
            _ensure_expected_account(page, account)
            previous_url = _latest_post_url(page, account)
            _publish_threads(page, video, caption)
            evidence = _wait_for_new_post(page, account, previous_url)
            return {
                **summary,
                "status": "CONFIRMED",
                "remote_id": evidence["remote_id"],
                "confirmation_evidence": {
                    "verified_id": evidence["remote_id"],
                    "permalink": evidence["permalink"],
                    "previous_latest": previous_url,
                },
            }
        finally:
            context.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--platform", choices=["threads"], default="threads")
    p.add_argument("--account", required=True)
    p.add_argument("--video", required=True)
    p.add_argument("--caption", default="")
    p.add_argument("--profile", required=True)
    p.add_argument("--commit", action="store_true")
    p.add_argument("--headed", action="store_true")
    args = p.parse_args()
    try:
        out = publish(
            args.platform, args.video, args.caption, args.account, args.profile,
            commit=args.commit, headless=not args.headed,
        )
    except AuthenticationRequired as exc:
        out = {"status": "AUTH_REQUIRED", "platform": "threads", "reason": str(exc)}
    except IdentityMismatch as exc:
        out = {"status": "IDENTITY_MISMATCH", "platform": "threads", "reason": str(exc)}
    except PublicationUnverified as exc:
        out = {"status": "UNCERTAIN", "platform": "threads", "reason": str(exc)}
    except BrowserPublishError as exc:
        out = {"status": "FAILED", "platform": "threads", "reason": str(exc)}
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
