#!/usr/bin/env python3
"""Browser UI publishers for Discord, LinkedIn, Medium, Rumble and Odysee.

These adapters use ordinary signed-in web sessions. They are fail-closed:
submission is reported as CONFIRMED only after a platform-specific target URL is
observed. Odysee is the canonical platform name; the common "odyssey" spelling
is accepted as an input alias.
"""
import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlsplit


SUPPORTED = frozenset(("discord", "linkedin", "medium", "rumble", "odysee"))
ALIASES = {"odyssey": "odysee"}


class BrowserPublishError(RuntimeError):
    pass


class AuthenticationRequired(BrowserPublishError):
    pass


class IdentityMismatch(BrowserPublishError):
    pass


class PublicationUnverified(BrowserPublishError):
    pass


def canonical_platform(value):
    value = str(value or "").strip().casefold()
    return ALIASES.get(value, value)


def normalize_account(value):
    return str(value or "").strip().lstrip("@").casefold()


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def external_id_from_url(platform, url):
    platform = canonical_platform(platform)
    parsed = urlsplit(url)
    parts = [p for p in parsed.path.split("/") if p]
    if platform == "discord" and len(parts) >= 4 and parts[0] == "channels":
        return parts[3]
    if platform == "linkedin":
        match = re.search(r"urn:li:activity:([0-9]+)", parsed.path)
        if not match:
            match = re.search(r"activity-([0-9]+)", parsed.path)
        return match.group(1) if match else ""
    if platform == "medium":
        return parts[-1] if len(parts) >= 2 and parts[0].startswith("@") else ""
    if platform == "rumble":
        return parts[-1] if parts and parts[-1].startswith("v") and parts[-1].endswith(".html") else ""
    if platform == "odysee":
        return parts[-1] if len(parts) >= 2 and any(p.startswith("@") for p in parts) else ""
    return ""


def canonical_post_url(platform, href):
    platform = canonical_platform(platform)
    if not href:
        return ""
    bases = {
        "discord": "https://discord.com",
        "linkedin": "https://www.linkedin.com",
        "medium": "https://medium.com",
        "rumble": "https://rumble.com",
        "odysee": "https://odysee.com",
    }
    if href.startswith("/"):
        href = urljoin(bases[platform], href)
    parsed = urlsplit(href)
    if parsed.scheme != "https":
        return ""
    host = (parsed.hostname or "").lower()

    if platform == "discord":
        if host not in {"discord.com", "www.discord.com"}:
            return ""
        match = re.fullmatch(r"/channels/([0-9]+)/([0-9]+)/([0-9]+)/?", parsed.path)
        return f"https://discord.com/channels/{match.group(1)}/{match.group(2)}/{match.group(3)}" if match else ""

    if platform == "linkedin":
        if host not in {"linkedin.com", "www.linkedin.com"}:
            return ""
        if "/feed/update/urn:li:activity:" not in parsed.path and "/posts/" not in parsed.path:
            return ""
        return f"https://www.linkedin.com{parsed.path.rstrip('/')}/"

    if platform == "medium":
        if host not in {"medium.com", "www.medium.com"}:
            return ""
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) < 2 or not parts[0].startswith("@"):
            return ""
        return f"https://medium.com/{parts[0]}/{parts[-1]}"

    if platform == "rumble":
        if host not in {"rumble.com", "www.rumble.com"}:
            return ""
        parts = [p for p in parsed.path.split("/") if p]
        if not parts or not parts[-1].startswith("v") or not parts[-1].endswith(".html"):
            return ""
        return f"https://rumble.com/{parts[-1]}"

    if platform == "odysee":
        if host not in {"odysee.com", "www.odysee.com"}:
            return ""
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) < 2 or not any(p.startswith("@") for p in parts):
            return ""
        return f"https://odysee.com/{'/'.join(parts)}"
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
        return page.locator("body").inner_text(timeout=3000) or ""
    except Exception:
        return ""


def _auth_wall(page, platform):
    platform = canonical_platform(platform)
    url = page.url.casefold()
    markers = {
        "discord": ("/login", "/register"),
        "linkedin": ("/login", "/authwall", "/checkpoint"),
        "medium": ("/m/signin", "/signin"),
        "rumble": ("/login", "/account/login"),
        "odysee": ("/signin", "/login"),
    }
    if any(marker in url for marker in markers.get(platform, ())):
        return True
    text = _body_text(page).casefold()
    needles = {
        "discord": ("log in to discord", "entrar no discord"),
        "linkedin": ("sign in to linkedin", "entrar no linkedin"),
        "medium": ("sign in to medium", "sign in with google"),
        "rumble": ("sign in to rumble", "login to rumble"),
        "odysee": ("sign in", "create an account"),
    }
    common = ("verify your identity", "confirme sua identidade", "security challenge")
    return any(n in text for n in needles.get(platform, ()) + common)


def _require_account_marker(page, platform, account):
    """Strict identity fence for sites without a stable API identity surface."""
    if not normalize_account(account):
        raise ValueError("account is required")
    if _auth_wall(page, platform):
        raise AuthenticationRequired(f"{platform}: login/session challenge detected")
    text = _body_text(page).casefold()
    account_norm = normalize_account(account)
    if account_norm not in text:
        raise IdentityMismatch(f"{platform}: expected account @{account_norm} could not be verified in the signed-in UI")


def _ensure_expected_account(page, platform, account, destination=""):
    platform = canonical_platform(platform)
    account = normalize_account(account)
    if platform == "discord":
        if not destination or not canonical_channel_url(destination):
            raise BrowserPublishError("discord: --destination must be a channel URL")
        page.goto(destination, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(1500)
        _require_account_marker(page, platform, account)
        return
    if platform == "linkedin":
        page.goto(f"https://www.linkedin.com/in/{account}/", wait_until="domcontentloaded", timeout=45000)
    elif platform == "medium":
        page.goto(f"https://medium.com/@{account}", wait_until="domcontentloaded", timeout=45000)
    elif platform == "rumble":
        page.goto("https://rumble.com/account/", wait_until="domcontentloaded", timeout=45000)
    elif platform == "odysee":
        page.goto(f"https://odysee.com/@{account}", wait_until="domcontentloaded", timeout=45000)
    else:
        raise ValueError("unsupported platform")
    page.wait_for_timeout(1500)
    _require_account_marker(page, platform, account)


def canonical_channel_url(url):
    if not url:
        return ""
    parsed = urlsplit(url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in {"discord.com", "www.discord.com"}:
        return ""
    match = re.fullmatch(r"/channels/([0-9]+)/([0-9]+)/?", parsed.path)
    return f"https://discord.com/channels/{match.group(1)}/{match.group(2)}" if match else ""


def _latest_linkedin(page, account):
    page.goto(f"https://www.linkedin.com/in/{normalize_account(account)}/recent-activity/all/", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1600)
    if _auth_wall(page, "linkedin"):
        raise AuthenticationRequired("linkedin: authentication required while checking recent activity")
    links = page.locator('a[href*="/feed/update/"], a[href*="/posts/"]')
    for i in range(min(links.count(), 50)):
        url = canonical_post_url("linkedin", links.nth(i).get_attribute("href") or "")
        if url and external_id_from_url("linkedin", url):
            return url
    return ""


def _latest_medium(page, account):
    page.goto(f"https://medium.com/@{normalize_account(account)}", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1400)
    if _auth_wall(page, "medium"):
        raise AuthenticationRequired("medium: authentication required while checking profile")
    links = page.locator('a[href*="medium.com/"]')
    for i in range(min(links.count(), 80)):
        url = canonical_post_url("medium", links.nth(i).get_attribute("href") or "")
        if url and external_id_from_url("medium", url):
            return url
    return ""


def _publish_discord(page, video, caption, destination):
    channel = canonical_channel_url(destination)
    if not channel:
        raise BrowserPublishError("discord: invalid destination channel URL")
    page.goto(channel, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1200)
    if _auth_wall(page, "discord"):
        raise AuthenticationRequired("discord: destination requires authentication")
    file_input = page.locator('input[type="file"]').first
    try:
        file_input.wait_for(state="attached", timeout=5000)
    except Exception as exc:
        raise BrowserPublishError("discord: attachment input not found") from exc
    file_input.set_input_files(str(video))
    page.wait_for_timeout(1500)
    editor = _first_visible([
        page.locator('[role="textbox"][contenteditable="true"]'),
        page.locator('div[contenteditable="true"]'),
        page.get_by_role("textbox"),
    ], timeout_ms=3000)
    if editor is None:
        raise BrowserPublishError("discord: message editor not found after attachment")
    if caption:
        editor.fill(caption)
    editor.press("Enter")
    page.wait_for_timeout(2200)
    messages = page.locator('[id^="chat-messages-"]')
    if messages.count() < 1:
        raise PublicationUnverified("discord: message submitted but no message container was observed")
    element_id = messages.nth(messages.count() - 1).get_attribute("id") or ""
    match = re.search(r"chat-messages-[0-9]+-([0-9]+)$", element_id)
    if not match:
        raise PublicationUnverified("discord: newest message id could not be extracted")
    return f"{channel}/{match.group(1)}"


def _publish_linkedin(page, video, caption):
    page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1400)
    if _auth_wall(page, "linkedin"):
        raise AuthenticationRequired("linkedin: feed requires authentication")
    starter = _first_visible([
        page.get_by_role("button", name=re.compile(r"Start a post|Começar uma publicação|Iniciar uma publicação", re.I)),
        page.get_by_text(re.compile(r"Start a post|Começar uma publicação|Iniciar uma publicação", re.I)),
    ], timeout_ms=3000)
    if starter is None:
        raise BrowserPublishError("linkedin: post composer control not found")
    starter.click()
    page.wait_for_timeout(800)
    video_control = _first_visible([
        page.get_by_role("button", name=re.compile(r"Video|Vídeo", re.I)),
        page.get_by_text(re.compile(r"^Video$|^Vídeo$", re.I)),
    ], timeout_ms=2000)
    if video_control is not None:
        video_control.click()
        page.wait_for_timeout(500)
    file_input = page.locator('input[type="file"]').first
    try:
        file_input.wait_for(state="attached", timeout=5000)
    except Exception as exc:
        raise BrowserPublishError("linkedin: video upload input not found") from exc
    file_input.set_input_files(str(video))
    editor = _first_visible([
        page.locator('[contenteditable="true"][role="textbox"]'),
        page.get_by_role("textbox"),
    ], timeout_ms=3500)
    if editor is None:
        raise BrowserPublishError("linkedin: post text editor not found")
    editor.fill(caption)
    post = _first_visible([
        page.get_by_role("button", name=re.compile(r"^Post$|^Publicar$", re.I)),
    ], timeout_ms=5000)
    if post is None:
        raise BrowserPublishError("linkedin: Post button not found")
    deadline = time.time() + 90
    while time.time() < deadline:
        try:
            if post.is_enabled():
                post.click()
                return
        except Exception:
            pass
        page.wait_for_timeout(1000)
    raise BrowserPublishError("linkedin: Post button never became enabled")


def _publish_medium(page, caption, media_url, title):
    if not media_url or not urlsplit(media_url).scheme.startswith("http"):
        raise BrowserPublishError("medium: --media-url is required for a video embed/link publication")
    page.goto("https://medium.com/new-story", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1400)
    if _auth_wall(page, "medium"):
        raise AuthenticationRequired("medium: editor requires authentication")
    editors = page.locator('[contenteditable="true"]')
    if editors.count() < 1:
        raise BrowserPublishError("medium: story editor not found")
    story_title = title.strip() if title else (caption.strip().splitlines()[0][:100] if caption.strip() else "Vídeo")
    first = editors.nth(0)
    first.fill(story_title)
    body = editors.nth(1) if editors.count() > 1 else first
    body.press("End")
    if caption:
        body.fill(caption)
        body.press("Enter")
    body.type(media_url)
    body.press("Enter")
    page.wait_for_timeout(1600)
    publish_control = _first_visible([
        page.get_by_role("button", name=re.compile(r"^Publish$|^Publicar$", re.I)),
        page.get_by_text(re.compile(r"^Publish$|^Publicar$", re.I)),
    ], timeout_ms=4000)
    if publish_control is None:
        raise BrowserPublishError("medium: Publish control not found")
    publish_control.click()
    page.wait_for_timeout(700)
    final_publish = _first_visible([
        page.get_by_role("button", name=re.compile(r"^Publish now$|^Publish$|^Publicar agora$|^Publicar$", re.I)),
    ], timeout_ms=3500)
    if final_publish is not None:
        final_publish.click()
    page.wait_for_timeout(2500)
    return canonical_post_url("medium", page.url)


def _publish_rumble(page, video, caption, title):
    page.goto("https://rumble.com/upload.php", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1300)
    if _auth_wall(page, "rumble"):
        raise AuthenticationRequired("rumble: uploader requires authentication")
    file_input = page.locator('input[type="file"]').first
    try:
        file_input.wait_for(state="attached", timeout=5000)
    except Exception as exc:
        raise BrowserPublishError("rumble: video upload input not found") from exc
    file_input.set_input_files(str(video))
    title_box = _first_visible([
        page.get_by_label(re.compile(r"Title|Título", re.I)),
        page.locator('input[name*="title" i]'),
        page.locator('input[placeholder*="title" i]'),
    ], timeout_ms=3500)
    if title_box is None:
        raise BrowserPublishError("rumble: title field not found")
    story_title = title.strip() if title else (caption.strip().splitlines()[0][:100] if caption.strip() else Path(video).stem)
    title_box.fill(story_title)
    description = _first_visible([
        page.get_by_label(re.compile(r"Description|Descrição", re.I)),
        page.locator('textarea[name*="description" i]'),
        page.locator('textarea'),
    ], timeout_ms=2500)
    if description is not None and caption:
        description.fill(caption)
    submit = _first_visible([
        page.get_by_role("button", name=re.compile(r"Upload|Submit|Publish|Enviar|Publicar", re.I)),
        page.locator('input[type="submit"]'),
    ], timeout_ms=4000)
    if submit is None:
        raise BrowserPublishError("rumble: upload submit control not found; account defaults/licensing may require setup")
    submit.click()
    page.wait_for_timeout(3000)
    return canonical_post_url("rumble", page.url)


def _publish_odysee(page, video, caption, title):
    page.goto("https://odysee.com/$/upload", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1400)
    if _auth_wall(page, "odysee"):
        raise AuthenticationRequired("odysee: uploader requires authentication")
    file_input = page.locator('input[type="file"]').first
    try:
        file_input.wait_for(state="attached", timeout=5000)
    except Exception as exc:
        raise BrowserPublishError("odysee: upload input not found") from exc
    file_input.set_input_files(str(video))
    title_box = _first_visible([
        page.get_by_label(re.compile(r"Title|Título", re.I)),
        page.locator('input[name*="title" i]'),
        page.locator('input[placeholder*="title" i]'),
    ], timeout_ms=3000)
    if title_box is None:
        raise BrowserPublishError("odysee: title field not found")
    story_title = title.strip() if title else (caption.strip().splitlines()[0][:100] if caption.strip() else Path(video).stem)
    title_box.fill(story_title)
    description = _first_visible([
        page.get_by_label(re.compile(r"Description|Descrição", re.I)),
        page.locator('textarea'),
        page.locator('[contenteditable="true"][role="textbox"]'),
    ], timeout_ms=2200)
    if description is not None and caption:
        description.fill(caption)
    upload = _first_visible([
        page.get_by_role("button", name=re.compile(r"Upload|Publish|Publicar|Enviar", re.I)),
    ], timeout_ms=4500)
    if upload is None:
        raise BrowserPublishError("odysee: publish control not found")
    upload.click()
    page.wait_for_timeout(3500)
    return canonical_post_url("odysee", page.url)


def _wait_new_linkedin(page, account, previous, timeout_seconds=120):
    deadline = time.time() + timeout_seconds
    last = ""
    while time.time() < deadline:
        last = _latest_linkedin(page, account)
        if last and last != previous:
            return last
        page.wait_for_timeout(2500)
    raise PublicationUnverified(f"linkedin: no new public post observed; last={last!r}")


def _wait_current_or_link(page, platform, immediate_url="", timeout_seconds=120):
    if immediate_url and external_id_from_url(platform, immediate_url):
        return immediate_url
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        current = canonical_post_url(platform, page.url)
        if current and external_id_from_url(platform, current):
            return current
        selector_map = {
            "medium": 'a[href*="medium.com/@"]',
            "rumble": 'a[href*="rumble.com/v"]',
            "odysee": 'a[href*="odysee.com/@"], a[href^="/@"]',
        }
        links = page.locator(selector_map.get(platform, "a"))
        for i in range(min(links.count(), 50)):
            candidate = canonical_post_url(platform, links.nth(i).get_attribute("href") or "")
            if candidate and external_id_from_url(platform, candidate):
                return candidate
        page.wait_for_timeout(2200)
    raise PublicationUnverified(f"{platform}: submit completed but no publication URL was observed")


def publish(platform, video, caption, account, profile, commit=False, headless=True,
            destination="", media_url="", title=""):
    platform = canonical_platform(platform)
    if platform not in SUPPORTED:
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
    if destination:
        summary["destination"] = destination
    if media_url:
        summary["media_url"] = media_url
    if not commit:
        return {**summary, "status": "DRY_RUN"}

    from playwright.sync_api import sync_playwright

    profile.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                str(profile), headless=headless, accept_downloads=False,
                viewport={"width": 1280, "height": 900},
            )
            page = context.pages[0] if context.pages else context.new_page()
            try:
                _ensure_expected_account(page, platform, account, destination)
                if platform == "discord":
                    url = _publish_discord(page, video, caption, destination)
                elif platform == "linkedin":
                    previous = _latest_linkedin(page, account)
                    _publish_linkedin(page, video, caption)
                    url = _wait_new_linkedin(page, account, previous)
                elif platform == "medium":
                    previous = _latest_medium(page, account)
                    immediate = _publish_medium(page, caption, media_url, title)
                    url = _wait_current_or_link(page, platform, immediate)
                    if previous and url == previous:
                        raise PublicationUnverified("medium: newest observed story did not change")
                elif platform == "rumble":
                    immediate = _publish_rumble(page, video, caption, title)
                    url = _wait_current_or_link(page, platform, immediate)
                else:
                    immediate = _publish_odysee(page, video, caption, title)
                    url = _wait_current_or_link(page, platform, immediate)
                remote_id = external_id_from_url(platform, url)
                if not remote_id:
                    raise PublicationUnverified(f"{platform}: publication URL lacks a stable id")
                return {
                    **summary,
                    "status": "CONFIRMED",
                    "remote_id": remote_id,
                    "confirmation_evidence": {"verified_id": remote_id, "permalink": url},
                }
            finally:
                context.close()
    except AuthenticationRequired as exc:
        return {**summary, "status": "AUTH_REQUIRED", "reason": str(exc)}
    except IdentityMismatch as exc:
        return {**summary, "status": "IDENTITY_MISMATCH", "reason": str(exc)}
    except PublicationUnverified as exc:
        return {**summary, "status": "UNCERTAIN", "reason": str(exc)}
    except BrowserPublishError as exc:
        return {**summary, "status": "FAILED", "reason": str(exc)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=["discord", "linkedin", "medium", "rumble", "odysee", "odyssey"], required=True)
    parser.add_argument("--video", required=True)
    parser.add_argument("--caption", default="")
    parser.add_argument("--title", default="")
    parser.add_argument("--account", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--destination", default="")
    parser.add_argument("--media-url", default="")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()
    out = publish(
        args.platform, args.video, args.caption, args.account, args.profile,
        commit=args.commit, headless=not args.headed,
        destination=args.destination, media_url=args.media_url, title=args.title,
    )
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
