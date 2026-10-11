#!/usr/bin/env python3
"""Browser UI publisher for personal X, Instagram and Facebook accounts.

The adapter behaves like an ordinary signed-in user through the web UI. It is
fail-closed around identity, authentication challenges and publication evidence:
a submit without independently observed public evidence is never reported as
published.
"""
import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlsplit


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


def external_id_from_url(platform, url):
    parts = [p for p in urlsplit(url).path.split("/") if p]
    if platform == "x":
        if "status" not in parts:
            return ""
        idx = parts.index("status")
        return parts[idx + 1] if idx + 1 < len(parts) else ""
    if platform == "instagram":
        for marker in ("reel", "p"):
            if marker in parts:
                idx = parts.index(marker)
                return parts[idx + 1] if idx + 1 < len(parts) else ""
    if platform == "facebook" and "reel" in parts:
        idx = parts.index("reel")
        return parts[idx + 1] if idx + 1 < len(parts) else ""
    return ""


def canonical_post_url(platform, account, href):
    if not href:
        return ""
    bases = {
        "x": "https://x.com",
        "instagram": "https://www.instagram.com",
        "facebook": "https://www.facebook.com",
    }
    if href.startswith("/"):
        href = urljoin(bases.get(platform, ""), href)
    parsed = urlsplit(href)
    if parsed.scheme != "https":
        return ""
    host = (parsed.hostname or "").lower()
    if platform == "x":
        if host not in {"x.com", "www.x.com", "twitter.com", "www.twitter.com"}:
            return ""
        match = re.search(r"/status/([0-9]+)", parsed.path)
        if not match:
            return ""
        return f"https://x.com/{normalize_account(account)}/status/{match.group(1)}"
    if platform == "instagram":
        if host not in {"instagram.com", "www.instagram.com"}:
            return ""
        match = re.search(r"/(reel|p)/([^/?#]+)/?", parsed.path)
        if not match:
            return ""
        return f"https://www.instagram.com/{match.group(1)}/{match.group(2)}/"
    if platform == "facebook":
        if host not in {"facebook.com", "www.facebook.com", "m.facebook.com"}:
            return ""
        match = re.search(r"/reel/([0-9]+)", parsed.path)
        if not match:
            return ""
        return f"https://www.facebook.com/reel/{match.group(1)}"
    return ""


def _first_visible(locators, timeout_ms=1200):
    for locator in locators:
        try:
            locator.first.wait_for(state="visible", timeout=timeout_ms)
            return locator.first
        except Exception:
            continue
    return None


def _body_text(page):
    try:
        return (page.locator("body").inner_text(timeout=3000) or "").lower()
    except Exception:
        return ""


def _auth_wall(page, platform):
    url = page.url.lower()
    if platform == "x" and ("/i/flow/login" in url or "/login" in url):
        return True
    if platform == "instagram" and ("/accounts/login" in url or "/challenge" in url):
        return True
    if platform == "facebook" and any(marker in url for marker in ("/login", "/checkpoint", "/recover")):
        return True
    text = _body_text(page)
    needles = (
        "log in to x", "sign in to x", "entrar no x",
        "log in to instagram", "entrar no instagram",
        "log into facebook", "log in to facebook", "entrar no facebook",
        "challenge", "verify your identity", "confirme sua identidade",
    )
    return any(n in text for n in needles)


def _profile_url(platform, account):
    account = normalize_account(account)
    if platform == "x":
        return f"https://x.com/{account}"
    if platform == "instagram":
        return f"https://www.instagram.com/{account}/"
    if platform == "facebook":
        return f"https://www.facebook.com/{account}/"
    raise ValueError("unsupported platform")


def _ensure_expected_account(page, platform, account):
    page.goto(_profile_url(platform, account), wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1800)
    if _auth_wall(page, platform):
        raise AuthenticationRequired(f"{platform}: login/session challenge detected")
    labels = r"Edit profile|Editar perfil"
    if platform == "facebook":
        labels = r"Edit profile|Editar perfil|Edit details|Editar detalhes"
    own_controls = [
        page.get_by_role("link", name=re.compile(labels, re.I)),
        page.get_by_role("button", name=re.compile(labels, re.I)),
    ]
    if _first_visible(own_controls, timeout_ms=1800) is None:
        raise IdentityMismatch(
            f"{platform}: expected account @{normalize_account(account)} is not verified as the signed-in owner"
        )


def _latest_post_url(page, platform, account):
    target = _profile_url(platform, account)
    if platform == "facebook":
        target = target.rstrip("/") + "/reels/"
    page.goto(target, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1500)
    if _auth_wall(page, platform):
        raise AuthenticationRequired(f"{platform}: authentication required while checking profile")
    if platform == "x":
        links = page.locator('a[href*="/status/"]')
    elif platform == "instagram":
        links = page.locator('a[href*="/reel/"], a[href*="/p/"]')
    else:
        links = page.locator('a[href*="/reel/"]')
    count = min(links.count(), 40)
    for i in range(count):
        href = links.nth(i).get_attribute("href")
        url = canonical_post_url(platform, account, href or "")
        if url:
            return url
    return ""


def _publish_x(page, video, caption):
    page.goto("https://x.com/compose/post", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1200)
    if _auth_wall(page, "x"):
        raise AuthenticationRequired("x: composer requires authentication")
    editor = _first_visible([
        page.locator('[data-testid="tweetTextarea_0"]'),
        page.locator('[contenteditable="true"]'),
        page.get_by_role("textbox"),
    ], timeout_ms=2500)
    if editor is None:
        raise BrowserPublishError("x: composer editor not found")
    file_input = page.locator('input[type="file"]').first
    file_input.set_input_files(str(video))
    page.wait_for_timeout(1600)
    editor.fill(caption)
    post = _first_visible([
        page.locator('[data-testid="tweetButton"]'),
        page.locator('[data-testid="tweetButtonInline"]'),
        page.get_by_role("button", name=re.compile(r"^Post$|^Publicar$", re.I)),
    ], timeout_ms=2500)
    if post is None:
        raise BrowserPublishError("x: post button not found")
    deadline = time.time() + 45
    while time.time() < deadline:
        try:
            if post.is_enabled():
                post.click()
                return
        except Exception:
            pass
        page.wait_for_timeout(750)
    raise BrowserPublishError("x: post button never became enabled after upload")


def _publish_instagram(page, video, caption):
    page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1500)
    if _auth_wall(page, "instagram"):
        raise AuthenticationRequired("instagram: home requires authentication")
    create = _first_visible([
        page.get_by_text(re.compile(r"^Create$|^Criar$", re.I)),
        page.get_by_role("link", name=re.compile(r"Create|Criar", re.I)),
        page.get_by_role("button", name=re.compile(r"Create|Criar", re.I)),
    ], timeout_ms=2500)
    if create is None:
        raise BrowserPublishError("instagram: create control not found")
    create.click()
    page.wait_for_timeout(800)
    file_input = page.locator('input[type="file"]').first
    file_input.set_input_files(str(video))
    page.wait_for_timeout(1800)
    for _ in range(2):
        nxt = _first_visible([
            page.get_by_role("button", name=re.compile(r"^Next$|^Avançar$", re.I)),
            page.get_by_text(re.compile(r"^Next$|^Avançar$", re.I)),
        ], timeout_ms=4000)
        if nxt is None:
            raise BrowserPublishError("instagram: next control not found")
        nxt.click()
        page.wait_for_timeout(1100)
    caption_box = _first_visible([
        page.locator('textarea[aria-label*="caption" i]'),
        page.locator('textarea'),
        page.locator('[contenteditable="true"]').last,
        page.get_by_role("textbox").last,
    ], timeout_ms=3000)
    if caption_box is None:
        raise BrowserPublishError("instagram: caption editor not found")
    caption_box.fill(caption)
    share = _first_visible([
        page.get_by_role("button", name=re.compile(r"^Share$|^Compartilhar$", re.I)),
        page.get_by_text(re.compile(r"^Share$|^Compartilhar$", re.I)),
    ], timeout_ms=3000)
    if share is None:
        raise BrowserPublishError("instagram: share control not found")
    share.click()


def _facebook_caption_box(page):
    return _first_visible([
        page.get_by_role("textbox", name=re.compile(r"Describe your reel|Descrição|Descreva|Say something|Diga algo", re.I)),
        page.locator('textarea[aria-label*="reel" i]'),
        page.locator('textarea'),
        page.locator('[contenteditable="true"][role="textbox"]'),
    ], timeout_ms=1200)


def _publish_facebook(page, video, caption):
    page.goto("https://www.facebook.com/reels/create/", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1500)
    if _auth_wall(page, "facebook"):
        raise AuthenticationRequired("facebook: Reel creator requires authentication")

    file_input = page.locator('input[type="file"]').first
    try:
        file_input.wait_for(state="attached", timeout=5000)
    except Exception as exc:
        raise BrowserPublishError("facebook: Reel upload input not found") from exc
    file_input.set_input_files(str(video))
    page.wait_for_timeout(2200)

    caption_box = _facebook_caption_box(page)
    for _ in range(3):
        if caption_box is not None:
            break
        nxt = _first_visible([
            page.get_by_role("button", name=re.compile(r"^Next$|^Avançar$|^Próximo$", re.I)),
            page.get_by_text(re.compile(r"^Next$|^Avançar$|^Próximo$", re.I)),
        ], timeout_ms=3500)
        if nxt is None:
            break
        nxt.click()
        page.wait_for_timeout(1200)
        if _auth_wall(page, "facebook"):
            raise AuthenticationRequired("facebook: authentication challenge during Reel creation")
        caption_box = _facebook_caption_box(page)

    if caption_box is None:
        raise BrowserPublishError("facebook: Reel description editor not found")
    caption_box.fill(caption)

    publish_button = _first_visible([
        page.get_by_role("button", name=re.compile(r"^Publish$|^Publicar$|^Share$|^Compartilhar$", re.I)),
        page.get_by_text(re.compile(r"^Publish$|^Publicar$|^Share$|^Compartilhar$", re.I)),
    ], timeout_ms=4000)
    if publish_button is None:
        raise BrowserPublishError("facebook: Reel publish control not found")

    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            if publish_button.is_enabled():
                publish_button.click()
                return
        except Exception:
            pass
        page.wait_for_timeout(900)
    raise BrowserPublishError("facebook: publish control never became enabled after upload")


def _wait_for_new_post(page, platform, account, previous_url, timeout_seconds=120):
    deadline = time.time() + timeout_seconds
    last = ""
    while time.time() < deadline:
        try:
            last = _latest_post_url(page, platform, account)
            if last and last != previous_url:
                external_id = external_id_from_url(platform, last)
                if external_id:
                    return {"remote_id": external_id, "permalink": last}
        except AuthenticationRequired:
            raise
        except Exception:
            pass
        page.wait_for_timeout(2500)
    raise PublicationUnverified(
        f"{platform}: submit completed but no new public post was independently observed; last={last!r}"
    )


def publish(platform, video, caption, account, profile, commit=False, headless=True):
    platform = platform.casefold()
    if platform not in ("x", "instagram", "facebook"):
        raise ValueError("unsupported platform")
    video = Path(video).resolve()
    profile = Path(profile).resolve()
    if not video.is_file():
        raise FileNotFoundError(video)
    if not normalize_account(account):
        raise ValueError("account is required")
    summary = {
        "platform": platform,
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
            str(profile),
            headless=headless,
            accept_downloads=False,
            viewport={"width": 1280, "height": 900},
        )
        page = context.pages[0] if context.pages else context.new_page()
        try:
            _ensure_expected_account(page, platform, account)
            previous_url = _latest_post_url(page, platform, account)
            publishers = {
                "x": _publish_x,
                "instagram": _publish_instagram,
                "facebook": _publish_facebook,
            }
            publishers[platform](page, video, caption)
            evidence = _wait_for_new_post(page, platform, account, previous_url)
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=["x", "instagram", "facebook"], required=True)
    parser.add_argument("--video", required=True)
    parser.add_argument("--caption", required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()
    try:
        out = publish(
            args.platform,
            args.video,
            args.caption,
            args.account,
            args.profile,
            commit=args.commit,
            headless=not args.headed,
        )
    except AuthenticationRequired as exc:
        out = {"status": "AUTH_REQUIRED", "platform": args.platform, "reason": str(exc)}
    except IdentityMismatch as exc:
        out = {"status": "IDENTITY_MISMATCH", "platform": args.platform, "reason": str(exc)}
    except PublicationUnverified as exc:
        out = {"status": "UNCERTAIN", "platform": args.platform, "reason": str(exc)}
    except BrowserPublishError as exc:
        out = {"status": "FAILED", "platform": args.platform, "reason": str(exc)}
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
