#!/usr/bin/env python3
"""Strategic browser-UI publisher for Pinterest Video Pins.

Unlike short-form social mirrors, Pinterest is treated as search/discovery:
every Pin carries a search-oriented title, semantic description, thematic board,
related-topic metadata and a directly related destination URL.
"""
import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from social_adapters.pinterest_strategy import build_strategy


class BrowserPublishError(RuntimeError):
    pass


class AuthenticationRequired(BrowserPublishError):
    pass


class IdentityMismatch(BrowserPublishError):
    pass


class PublicationUnverified(BrowserPublishError):
    pass


class BoardUnavailable(BrowserPublishError):
    pass


def normalize_account(value):
    return str(value or "").strip().lstrip("@").casefold()


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _valid_destination(url):
    try:
        parsed = urlsplit(str(url or "").strip())
        return parsed.scheme in {"https", "http"} and bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        return False


def external_id_from_url(url):
    parsed = urlsplit(url)
    match = re.search(r"/pin/([0-9]+)(?:/|$)", parsed.path)
    return match.group(1) if match else ""


def canonical_post_url(href):
    if not href:
        return ""
    if href.startswith("/"):
        href = urljoin("https://www.pinterest.com", href)
    parsed = urlsplit(href)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in {"pinterest.com", "www.pinterest.com"}:
        return ""
    pin_id = external_id_from_url(href)
    return f"https://www.pinterest.com/pin/{pin_id}/" if pin_id else ""


def _first_visible(locators, timeout_ms=1300):
    for locator in locators:
        try:
            locator.first.wait_for(state="visible", timeout=timeout_ms)
            return locator.first
        except Exception:
            continue
    return None


def _body_text(page):
    try:
        return (page.locator("body").inner_text(timeout=3000) or "").casefold()
    except Exception:
        return ""


def _auth_wall(page):
    url = page.url.casefold()
    if any(marker in url for marker in ("/login", "/oauth", "/signup")):
        return True
    text = _body_text(page)
    needles = (
        "log in to pinterest", "entrar no pinterest", "continue with google",
        "continuar com o google", "verify your identity", "confirme sua identidade",
    )
    return any(n.casefold() in text for n in needles)


def _profile_url(account):
    return f"https://www.pinterest.com/{normalize_account(account)}/"


def _ensure_expected_account(page, account):
    page.goto(_profile_url(account), wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1600)
    if _auth_wall(page):
        raise AuthenticationRequired("pinterest: login/session challenge detected")
    own = _first_visible([
        page.get_by_role("button", name=re.compile(r"Edit profile|Editar perfil", re.I)),
        page.get_by_role("link", name=re.compile(r"Edit profile|Editar perfil", re.I)),
        page.get_by_text(re.compile(r"^Edit profile$|^Editar perfil$", re.I)),
    ], timeout_ms=2200)
    if own is None:
        raise IdentityMismatch(
            f"pinterest: expected account @{normalize_account(account)} is not verified as the signed-in owner"
        )


def _latest_pin_url(page, account):
    candidates = [
        _profile_url(account).rstrip("/") + "/_created/",
        _profile_url(account),
    ]
    for target in candidates:
        page.goto(target, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(1400)
        if _auth_wall(page):
            raise AuthenticationRequired("pinterest: authentication required while checking created Pins")
        links = page.locator('a[href*="/pin/"]')
        for i in range(min(links.count(), 50)):
            url = canonical_post_url(links.nth(i).get_attribute("href") or "")
            if url:
                return url
    return ""


def _fill(locator, value):
    if locator is None:
        return False
    try:
        locator.fill(value)
        return True
    except Exception:
        try:
            locator.click()
            locator.press("Control+A")
            locator.type(value)
            return True
        except Exception:
            return False


def _select_or_create_board(page, board):
    chooser = _first_visible([
        page.get_by_role("button", name=re.compile(r"Choose a board|Select board|Escolha uma pasta|Selecionar pasta|Pasta", re.I)),
        page.locator('[data-test-id*="board" i]').filter(has_text=re.compile(r"board|pasta", re.I)),
    ], timeout_ms=2500)
    if chooser is None:
        raise BoardUnavailable("pinterest: board chooser not found")
    chooser.click()
    page.wait_for_timeout(500)

    search = _first_visible([
        page.get_by_role("textbox", name=re.compile(r"Search.*board|Pesquisar.*pasta", re.I)),
        page.locator('input[placeholder*="board" i]'),
        page.locator('input[placeholder*="pasta" i]'),
    ], timeout_ms=1200)
    if search is not None:
        _fill(search, board)
        page.wait_for_timeout(450)

    exact = _first_visible([
        page.get_by_text(board, exact=True),
        page.get_by_role("button", name=re.compile(rf"^{re.escape(board)}$", re.I)),
    ], timeout_ms=1800)
    if exact is not None:
        exact.click()
        return

    create = _first_visible([
        page.get_by_role("button", name=re.compile(r"Create board|Criar pasta", re.I)),
        page.get_by_text(re.compile(r"^Create board$|^Criar pasta$", re.I)),
    ], timeout_ms=1500)
    if create is None:
        raise BoardUnavailable(f"pinterest: board {board!r} not found and create-board control unavailable")
    create.click()
    page.wait_for_timeout(450)
    name_box = _first_visible([
        page.get_by_role("textbox", name=re.compile(r"Name|Nome", re.I)),
        page.locator('input[placeholder*="name" i]'),
        page.locator('input[placeholder*="nome" i]'),
    ], timeout_ms=1800)
    if name_box is None or not _fill(name_box, board):
        raise BoardUnavailable("pinterest: create-board name field not found")
    submit = _first_visible([
        page.get_by_role("button", name=re.compile(r"^Create$|^Criar$", re.I)),
        page.get_by_text(re.compile(r"^Create$|^Criar$", re.I)),
    ], timeout_ms=1800)
    if submit is None:
        raise BoardUnavailable("pinterest: create-board submit control not found")
    submit.click()
    page.wait_for_timeout(700)


def _tag_topics(page, topics):
    opener = _first_visible([
        page.get_by_text(re.compile(r"Tag related topics|Marcar interesses relacionados", re.I)),
        page.get_by_role("button", name=re.compile(r"related topics|interesses relacionados", re.I)),
    ], timeout_ms=700)
    if opener is None:
        return 0
    try:
        opener.click()
        page.wait_for_timeout(350)
    except Exception:
        return 0
    tagged = 0
    for topic in topics[:10]:
        item = _first_visible([
            page.get_by_text(re.compile(rf"^{re.escape(topic)}$", re.I)),
            page.get_by_role("option", name=re.compile(re.escape(topic), re.I)),
        ], timeout_ms=350)
        if item is None:
            continue
        try:
            item.click()
            tagged += 1
        except Exception:
            continue
    return tagged


def _publish_pin(page, video, strategy, destination_url):
    page.goto("https://www.pinterest.com/pin-creation-tool/", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(1400)
    if _auth_wall(page):
        raise AuthenticationRequired("pinterest: Pin creator requires authentication")

    file_input = page.locator('input[type="file"]').first
    try:
        file_input.wait_for(state="attached", timeout=6000)
    except Exception as exc:
        raise BrowserPublishError("pinterest: video upload input not found") from exc
    file_input.set_input_files(str(video))
    page.wait_for_timeout(1800)

    title_box = _first_visible([
        page.get_by_role("textbox", name=re.compile(r"title|título", re.I)),
        page.locator('input[placeholder*="title" i]'),
        page.locator('input[placeholder*="título" i]'),
    ], timeout_ms=2500)
    if title_box is None or not _fill(title_box, strategy.title):
        raise BrowserPublishError("pinterest: title field not found")

    desc_box = _first_visible([
        page.get_by_role("textbox", name=re.compile(r"description|descrição|tell everyone", re.I)),
        page.locator('textarea'),
        page.locator('[contenteditable="true"][role="textbox"]'),
    ], timeout_ms=2500)
    if desc_box is None or not _fill(desc_box, strategy.description):
        raise BrowserPublishError("pinterest: description field not found")

    link_box = _first_visible([
        page.get_by_role("textbox", name=re.compile(r"link|URL|site", re.I)),
        page.locator('input[type="url"]'),
        page.locator('input[placeholder*="link" i]'),
        page.locator('input[placeholder*="url" i]'),
    ], timeout_ms=2500)
    if link_box is None or not _fill(link_box, destination_url):
        raise BrowserPublishError("pinterest: destination link field not found")

    _select_or_create_board(page, strategy.board)
    tagged = _tag_topics(page, strategy.topics)

    publish_button = _first_visible([
        page.get_by_role("button", name=re.compile(r"^Publish$|^Publicar$", re.I)),
        page.get_by_text(re.compile(r"^Publish$|^Publicar$", re.I)),
    ], timeout_ms=3500)
    if publish_button is None:
        raise BrowserPublishError("pinterest: publish control not found")
    deadline = time.time() + 75
    while time.time() < deadline:
        try:
            if publish_button.is_enabled():
                publish_button.click()
                return tagged
        except Exception:
            pass
        page.wait_for_timeout(900)
    raise BrowserPublishError("pinterest: publish control never became enabled after upload")


def _wait_for_new_pin(page, account, previous_url, timeout_seconds=120):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        current = canonical_post_url(page.url)
        if current and current != previous_url:
            return current
        try:
            latest = _latest_pin_url(page, account)
            if latest and latest != previous_url:
                return latest
        except AuthenticationRequired:
            raise
        except Exception:
            pass
        page.wait_for_timeout(2500)
    raise PublicationUnverified("pinterest: submit completed but no new public Pin URL was independently observed")


def publish(
    video,
    caption,
    account,
    profile,
    destination_url,
    title="",
    description="",
    board="",
    commit=False,
    headless=True,
):
    video = Path(video).resolve()
    profile = Path(profile).resolve()
    if not video.is_file():
        raise FileNotFoundError(video)
    if video.suffix.casefold() not in {".mp4", ".m4v"}:
        raise ValueError("pinterest web video Pins require .mp4 or .m4v")
    if not normalize_account(account):
        raise ValueError("account is required")
    if not _valid_destination(destination_url):
        raise ValueError("pinterest destination_url must be a direct http(s) URL related to the Pin")

    strategy = build_strategy(caption, title=title, description=description, board=board)
    summary = {
        "platform": "pinterest",
        "account": normalize_account(account),
        "video": str(video),
        "content_sha256": file_sha256(video),
        "destination_url": destination_url,
        "strategy": {
            "bucket": strategy.bucket,
            "distribution_weight": strategy.weight,
            "board": strategy.board,
            "title": strategy.title,
            "description": strategy.description,
            "topics": list(strategy.topics),
        },
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
            _ensure_expected_account(page, account)
            previous_url = _latest_pin_url(page, account)
            tagged = _publish_pin(page, video, strategy, destination_url)
            permalink = _wait_for_new_pin(page, account, previous_url)
            remote_id = external_id_from_url(permalink)
            if not remote_id:
                raise PublicationUnverified("pinterest: confirmed URL did not contain a Pin ID")
            return {
                **summary,
                "status": "CONFIRMED",
                "remote_id": remote_id,
                "topics_tagged_in_ui": tagged,
                "confirmation_evidence": {
                    "verified_id": remote_id,
                    "permalink": permalink,
                    "previous_latest": previous_url,
                },
            }
        finally:
            context.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--account", required=True)
    p.add_argument("--video", required=True)
    p.add_argument("--caption", default="")
    p.add_argument("--title", default="")
    p.add_argument("--description", default="")
    p.add_argument("--board", default="")
    p.add_argument("--destination-url", required=True)
    p.add_argument("--profile", required=True)
    p.add_argument("--commit", action="store_true")
    p.add_argument("--headed", action="store_true")
    args = p.parse_args()
    try:
        out = publish(
            video=args.video,
            caption=args.caption,
            account=args.account,
            profile=args.profile,
            destination_url=args.destination_url,
            title=args.title,
            description=args.description,
            board=args.board,
            commit=args.commit,
            headless=not args.headed,
        )
    except AuthenticationRequired as exc:
        out = {"status": "AUTH_REQUIRED", "platform": "pinterest", "reason": str(exc)}
    except IdentityMismatch as exc:
        out = {"status": "IDENTITY_MISMATCH", "platform": "pinterest", "reason": str(exc)}
    except PublicationUnverified as exc:
        out = {"status": "UNCERTAIN", "platform": "pinterest", "reason": str(exc)}
    except BrowserPublishError as exc:
        out = {"status": "FAILED", "platform": "pinterest", "reason": str(exc)}
    print(json.dumps(out, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
