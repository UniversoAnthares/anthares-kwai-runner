#!/usr/bin/env python3
"""Optional TikTok comment AFTER a remotely confirmed CORTES publication.

Two isolated accounts use the same implementation, each with its own Neon
comment receipt table. The irreversible comment click is always preceded by
an atomic source-video reservation. Ambiguous results are never retried.
"""
from __future__ import annotations

import os
import random
import re
import time
from urllib.parse import quote, urlsplit

VIDEO_RE = re.compile(r"^/(@[A-Za-z0-9._-]+)/video/(\d{12,25})/?$")
ID_RE = re.compile(r"^\d{12,25}$")
ACCOUNT_RE = re.compile(r"^[A-Za-z0-9._-]{2,64}$")
RNG = random.SystemRandom()
COMMENT_LIBRARY = (
    "Obrigado por compartilhar este conteúdo.",
    "Interessante conhecer essa perspectiva.",
    "Valeu por compartilhar essa ideia.",
    "Gostei da forma como o assunto foi apresentado.",
    "Esse assunto merece uma conversa mais longa.",
    "Interessante acompanhar diferentes opiniões sobre isso.",
    "É bom encontrar conteúdos que estimulam a curiosidade.",
    "Obrigado por trazer esse assunto.",
    "Essa é uma perspectiva que vale considerar.",
    "O tema rende uma boa discussão.",
    "Gostei de conhecer mais sobre esse assunto.",
    "Vale a pena continuar essa conversa.",
    "Esse assunto sempre traz novas perguntas.",
    "Obrigado por dedicar tempo a esse conteúdo.",
    "Uma contribuição interessante para a conversa.",
    "A apresentação ficou bem organizada.",
    "Que bom encontrar esse tema por aqui.",
    "O assunto permite várias interpretações.",
    "Valeu por dividir esse conhecimento.",
    "Interessante acompanhar esse raciocínio.",
    "Gostei de ouvir essa explicação.",
    "Uma reflexão que merece atenção.",
    "O conteúdo apresenta uma questão interessante.",
    "Obrigado por apresentar esse ponto de vista.",
    "Essa abordagem chama a atenção.",
    "Gostei de acompanhar a explicação.",
    "Uma boa oportunidade de aprender mais.",
    "Esse tema tem muitos detalhes interessantes.",
    "O assunto foi apresentado com clareza.",
    "É interessante considerar essas questões.",
    "Valeu pelo tempo dedicado ao vídeo.",
    "Gostei de ver o tema sendo discutido.",
    "Obrigado por abrir essa conversa.",
    "Uma perspectiva que acrescenta à discussão.",
    "Bacana encontrar conteúdos sobre esse tema.",
    "Esse tópico vale uma segunda conversa.",
    "Interessante perceber outros aspectos do assunto.",
    "Gostei de acompanhar esse conteúdo até o fim.",
    "O tema sempre desperta curiosidade.",
    "Uma contribuição valiosa para quem se interessa pelo tema.",
    "É bom ouvir diferentes maneiras de abordar isso.",
    "Obrigado pelo conteúdo e pela explicação.",
    "A discussão pode render bastante.",
    "Vale a pena pesquisar mais sobre esse assunto.",
    "Interessante perceber como esse tema é amplo.",
    "Esse vídeo abre espaço para novas perguntas.",
    "Gostei da organização das ideias.",
    "Obrigado por trazer mais uma perspectiva.",
    "Esse tema tem muito a oferecer.",
    "O assunto ficou interessante nessa apresentação.",
    "Bom encontrar mais gente falando sobre esse tema.",
    "Esse conteúdo contribui para ampliar a discussão.",
    "Valeu por compartilhar sua experiência.",
    "Interessante ver o assunto por esse ângulo.",
    "Gostei do cuidado com a apresentação.",
    "Esse vídeo traz um bom ponto para conversar.",
    "Uma maneira interessante de apresentar o tema.",
    "Obrigado por disponibilizar essa explicação.",
    "O tema tem diversas possibilidades de análise.",
    "Vale a pena ouvir opiniões diferentes sobre isso.",
)


def select_message(recent: list[dict] | None, rng=RNG) -> str:
    """Do not repeat any of the 30 most recent attempted messages."""
    used = {str(item.get("comment_text") or "").strip().casefold()
            for item in (recent or [])[:30] if isinstance(item, dict)}
    available = [value for value in COMMENT_LIBRARY if value.casefold() not in used]
    if not available:
        raise ValueError("TIKTOK_COMMENT_LIBRARY_EXHAUSTED")
    return rng.choice(available)


def normalize_candidate(url: str, account: str) -> tuple[str, str] | None:
    try:
        parts = urlsplit(url)
    except ValueError:
        return None
    if parts.scheme != "https" or parts.hostname not in ("www.tiktok.com", "tiktok.com"):
        return None
    match = VIDEO_RE.fullmatch(parts.path)
    if not match or match.group(1)[1:].casefold() in {
        account.casefold(), "universo.anthares", "lucasrosalem4"
    }:
        return None
    return "https://www.tiktok.com" + parts.path, match.group(2)


def guard_page(page) -> None:
    """Stop on visible login/captcha challenges, without flagging hidden widgets."""
    if "/login" in str(page.url).lower():
        raise RuntimeError("TIKTOK_COMMENT_LOGIN_REQUIRED")
    for selector in ("#loginModalContentContainer", "input[type='password']"):
        nodes = page.locator(selector)
        if nodes.count() and nodes.first.is_visible(timeout=400):
            raise RuntimeError("TIKTOK_COMMENT_LOGIN_REQUIRED")
    for selector in ("iframe[src*='captcha']", "[id*='captcha']",
                     "[data-e2e*='captcha']"):
        nodes = page.locator(selector)
        if nodes.count() and nodes.first.is_visible(timeout=400):
            raise RuntimeError("TIKTOK_COMMENT_SECURITY_CHALLENGE")

def verify_owner(page, account: str) -> None:
    page.goto("https://www.tiktok.com/profile", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(1000)
    guard_page(page)
    actual = re.search(r"tiktok\.com/@([^/?#]+)", str(page.url), re.I)
    if actual and actual.group(1).casefold() == account.casefold():
        return
    # TikTok sometimes holds /profile while hydrating. The account proof
    # must be positive before interacting with another person's video.
    try:
        raw = page.locator("#__UNIVERSAL_DATA_FOR_REHYDRATION__").text_content(timeout=3000)
        import json
        data = json.loads(raw or "{}")
        user = data.get("__DEFAULT_SCOPE__", {}).get("webapp.app-context", {}).get("user", {})
        if str(user.get("uniqueId") or "").casefold() == account.casefold():
            return
    except (ValueError, TypeError, AttributeError, KeyError):
        pass
    raise RuntimeError("TIKTOK_COMMENT_OWNER_UNVERIFIED")


def comment_editor(page):
    """Return a fillable comment composer, excluding non-editable wrapper divs."""
    selectors = (
        '[data-e2e="comment-input"] [contenteditable="true"]',
        '[data-e2e="comment-input"][contenteditable="true"]',
        'div[contenteditable="true"][data-e2e*="comment"]',
        'textarea[data-e2e*="comment"]',
        'div[contenteditable="true"][aria-label*="comment" i]',
        'textarea[placeholder*="comment" i]',
        'textarea[placeholder*="coment" i]',
    )
    for selector in selectors:
        nodes = page.locator(selector)
        if nodes.count():
            node = nodes.first
            try:
                if node.is_visible(timeout=1100):
                    return node
            except Exception:
                pass
    return None


def open_comment_editor(page):
    """Open only the visibly labelled comments panel, never engagement actions."""
    existing = comment_editor(page)
    if existing:
        return existing
    for selector in (
        '[aria-label^="Read or add comments"]',
        '[data-e2e="browse-comment-icon"]',
        '[data-e2e="comment-icon"]',
        'button[aria-label*="comment" i]',
        'button[aria-label*="coment" i]',
    ):
        nodes = page.locator(selector)
        if not nodes.count():
            continue
        control = nodes.first
        try:
            if not control.is_visible(timeout=650):
                continue
            guard_page(page)
            control.click(timeout=5000)
            page.wait_for_timeout(900)
            guard_page(page)
            return comment_editor(page)
        except RuntimeError:
            raise
        except Exception:
            continue
    return None

def comment_submit(page, *, require_enabled=True):
    for selector in (
        '[data-e2e="comment-post"]',
        'button[data-e2e*="comment-post"]',
        '[data-e2e="comment-submit"]',
    ):
        nodes = page.locator(selector)
        if nodes.count():
            node = nodes.first
            try:
                if node.is_visible(timeout=900) and (not require_enabled or node.is_enabled(timeout=900)):
                    return node
            except Exception:
                pass
    return None


def scroll_discovery(page):
    """Scroll TikTok's actual virtualized feed; use window on Explore pages."""
    return page.evaluate("""() => {
        const feed=document.querySelector('#column-list-container');
        if (feed) {
            const before=feed.scrollTop;
            feed.scrollTop=Math.min(feed.scrollHeight,
                                    feed.scrollTop+Math.max(650,feed.clientHeight));
            return {container:'feed',before,after:feed.scrollTop};
        }
        const before=window.scrollY;
        window.scrollBy(0,Math.max(700,Math.round(window.innerHeight*0.85)));
        return {container:'window',before,after:window.scrollY};
    }""")


def collect_video_urls(page, account, excluded, urls):
    """Collect only TikTok's actual rendered canonical links, never guessed IDs."""
    links = page.locator('a[href*="/video/"]').evaluate_all(
        "(xs) => xs.slice(0, 250).map(x => x.href)"
    )
    added = 0
    for url in list(links) + [str(page.url)]:
        entry = normalize_candidate(str(url), account)
        if entry and entry[1] not in excluded and entry[1] not in urls:
            urls[entry[1]] = entry[0]
            added += 1
    return added


def select_target(page, account: str, recent: list[dict], rng=RNG):
    """Start at the homepage and browse the real feed/Explore with bounded scrolling."""
    excluded = {str(x.get("target_video_id") or "")
                for x in recent[:30] if isinstance(x, dict)}
    urls: dict[str, str] = {}
    # Live proof on Nov 22: / routes primary to Explore, while secondary has a
    # virtualized For You list. Both yield real video links only after scrolling.
    for label, origin in (
        ("home", "https://www.tiktok.com/"),
        ("explore", "https://www.tiktok.com/explore"),
        ("foryou", "https://www.tiktok.com/foryou"),
        ("video-search", "https://www.tiktok.com/search/video?q=" + quote("livros")),
        ("literature-search", "https://www.tiktok.com/search?q=" + quote("literatura")),
        ("books", "https://www.tiktok.com/tag/livros"),
    ):
        page.goto(origin, wait_until="domcontentloaded", timeout=30000)
        guard_page(page)
        for step in range(6):
            page.wait_for_timeout(rng.randint(1500, 2150))
            guard_page(page)
            try:
                collect_video_urls(page, account, excluded, urls)
            except Exception:
                pass
            if len(urls) >= 8 and step >= 2:
                break
            scroll_discovery(page)
        print("TIKTOK_POST_COMMENT_DISCOVERY account=" + account +
              " source=" + label + " eligible_links=" + str(len(urls)), flush=True)
        if urls:
            break
    ids = list(urls)
    rng.shuffle(ids)
    for video_id in ids[:12]:
        try:
            page.goto(urls[video_id], wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(1300)
            guard_page(page)
            canonical = normalize_candidate(str(page.url), account)
            if not canonical or canonical[1] != video_id:
                continue
            if open_comment_editor(page):
                print("TIKTOK_POST_COMMENT_TARGET_READY account=" + account +
                      " id=" + video_id, flush=True)
                return video_id, urls[video_id]
        except RuntimeError:
            raise
        except Exception:
            continue
    return None

def post_comment_once(page, message: str) -> bool:
    editor = comment_editor(page)
    if editor is None:
        raise RuntimeError("TIKTOK_COMMENT_EDITOR_UNAVAILABLE")
    editor.fill(message, timeout=6000)
    present = (editor.input_value(timeout=2000)
               if editor.evaluate("(el)=>el.tagName") in ("TEXTAREA", "INPUT")
               else editor.inner_text(timeout=2000))
    if message not in present:
        raise RuntimeError("TIKTOK_COMMENT_EDITOR_READBACK_FAILED")
    button = comment_submit(page)
    if button is None:
        raise RuntimeError("TIKTOK_COMMENT_BUTTON_UNAVAILABLE")
    guard_page(page)
    button.click(timeout=7000)  # ONE irreversible click; never retry.
    page.wait_for_timeout(1800)
    guard_page(page)
    # Editor text is not sufficient: seek a posted comment in the comments list.
    for selector in (
        '[data-e2e="comment-level-1"]',
        '[data-e2e*="comment-item"]',
        '[data-e2e*="comment-text"]',
    ):
        if page.locator(selector).filter(has_text=message).count():
            return True
    return False


def after_confirmed(*, account: str, source_video_id: str, recent_call,
                    reserve_call, complete_call, storage_state=None,
                    existing_page=None) -> str:
    """Best-effort companion action; publish/confirm must never depend on it."""
    if os.getenv("TIKTOK_POST_COMMENT_ENABLED", "true").strip().lower() in ("0", "false", "off", "no"):
        return "disabled"
    if (not ACCOUNT_RE.fullmatch(account) or
            account.casefold() not in ("universo.anthares", "lucasrosalem4") or
            not ID_RE.fullmatch(str(source_video_id))):
        return "identity_invalid"
    reserved = False
    target_id = ""
    browser = None
    context = None
    page = existing_page
    try:
        recent_result = recent_call()
        if not isinstance(recent_result, dict) or not recent_result.get("ok"):
            return "history_unavailable"
        recent = recent_result.get("recent") or []
        message = select_message(recent)
        if page is None:
            if not isinstance(storage_state, dict):
                return "session_unavailable"
            from playwright.sync_api import sync_playwright
            # Explicit lifecycle; the private browser is owned by this action.
            with sync_playwright() as runtime:
                browser = runtime.chromium.launch(
                    headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
                try:
                    context = browser.new_context(
                        storage_state=storage_state, locale="pt-BR",
                        viewport={"width": 1280, "height": 900})
                    page = context.new_page()
                    return _execute(page, account, source_video_id, recent, message,
                                    reserve_call, complete_call)
                finally:
                    if context is not None:
                        context.close()
                    browser.close()
        return _execute(page, account, source_video_id, recent, message,
                        reserve_call, complete_call)
    except Exception as exc:
        # A comment error never marks an already confirmed video as uncertain.
        print("TIKTOK_POST_COMMENT_HOLD=" + type(exc).__name__, flush=True)
        return "unavailable"


def _execute(page, account, source_video_id, recent, message, reserve_call, complete_call):
    verify_owner(page, account)
    target = select_target(page, account, recent)
    if not target:
        print("TIKTOK_POST_COMMENT_NO_ELIGIBLE_TARGET=1", flush=True)
        return "no_target"
    target_id, _ = target
    payload = {"source_video_id": source_video_id, "target_video_id": target_id,
               "comment_text": message}
    reservation = reserve_call(payload)
    if not isinstance(reservation, dict) or reservation.get("reserved") is not True:
        print("TIKTOK_POST_COMMENT_ALREADY_RESERVED_OR_DENIED=1", flush=True)
        return "already_reserved"
    status = "uncertain"
    try:
        if post_comment_once(page, message):
            status = "posted"
    finally:
        # A timeout before/after click is always uncertain and never replayed.
        try:
            complete_call({"source_video_id": source_video_id,
                           "target_video_id": target_id, "status": status})
        except Exception:
            print("TIKTOK_POST_COMMENT_RECEIPT_UNCERTAIN=1", flush=True)
    print("TIKTOK_POST_COMMENT_RESULT=" + status + " account=" + account, flush=True)
    return status
