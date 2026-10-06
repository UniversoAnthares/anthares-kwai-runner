import os
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

import publisher_common as pc
import tiktok_worker as tw

VERSION = "0.1.0"
MODE = os.getenv("ATD_PUBLISH_MODE", "probe").strip().lower()
QUEUE_ID = int(os.getenv("ATD_QUEUE_ID", "0") or 0)
ARTIFACT_DIR = Path(os.getenv("ATD_ARTIFACT_DIR", "publisher-artifacts"))
UPLOAD_URLS = (
    "https://www.tiktok.com/tiktokstudio/upload?from=webapp",
    "https://www.tiktok.com/upload?lang=pt-BR",
)

SUCCESS_RE = re.compile(
    r"successfully posted|post published|your video has been posted|"
    r"publicado com sucesso|vídeo publicado|video publicado|foi publicado",
    re.I,
)
HUMAN_RE = re.compile(
    r"captcha|verify to continue|security check|unusual traffic|"
    r"verifique para continuar|confirme que você|verificação de segurança",
    re.I,
)


def screenshot(page, name):
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        page.screenshot(path=str(ARTIFACT_DIR / name), full_page=True)
    except Exception:
        pass


def page_text(page, limit=25000):
    try:
        return page.locator("body").inner_text(timeout=5000)[:limit]
    except Exception:
        return ""


def ensure_session(page, context):
    if tw.challenge_detected(page):
        raise RuntimeError("TikTok apresentou CAPTCHA/verificação.")
    cookies = context.cookies("https://www.tiktok.com")
    auth = tw.auth_cookie_names({"cookies": cookies})
    if not auth or tw.login_visible(page):
        raise RuntimeError("Sessão TikTok expirada ou desconectada.")


def open_upload(page, context):
    last_error = None
    for url in UPLOAD_URLS:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=90000)
            time.sleep(4)
            ensure_session(page, context)
            locator = page.locator('input[type="file"]')
            locator.first.wait_for(state="attached", timeout=30000)
            return locator.first
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Página de upload do TikTok indisponível: {last_error}")


def enabled_post_button(page):
    selectors = (
        'button:has-text("Post")',
        'button:has-text("Publicar")',
        'button:has-text("Publish")',
    )
    for selector in selectors:
        loc = page.locator(selector)
        count = loc.count()
        for i in range(count):
            button = loc.nth(i)
            try:
                if button.is_visible() and button.is_enabled():
                    return button
            except Exception:
                continue
    return None


def wait_upload_ready(page, timeout_seconds=360):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if tw.challenge_detected(page) or HUMAN_RE.search(page_text(page, 12000)):
            raise RuntimeError("TikTok solicitou CAPTCHA/verificação durante o upload.")
        button = enabled_post_button(page)
        if button is not None:
            return button
        time.sleep(3)
    raise RuntimeError("O botão Publicar não ficou disponível dentro do tempo limite.")


def handle_auto_checks_modal(page):
    selectors = (
        'button:has-text("Ativar")',
        'button:has-text("Enable")',
    )
    for selector in selectors:
        loc = page.locator(selector)
        try:
            if loc.first.is_visible(timeout=1200):
                loc.first.click(timeout=10000)
                time.sleep(2)
                return True
        except Exception:
            pass
    return False


def set_public_visibility(page):
    text = page_text(page, 22000)
    if re.search(r"\bTodos\b|\bEveryone\b|Público|Public", text, re.I):
        return True

    current_labels = ("Seguidores", "Followers", "Amigos", "Friends", "Somente você", "Apenas você", "Only you")
    opened = False
    for label in current_labels:
        loc = page.get_by_text(label, exact=True)
        try:
            if loc.first.is_visible(timeout=700):
                loc.first.click(timeout=8000)
                time.sleep(1)
                opened = True
                break
        except Exception:
            pass

    if opened:
        for label in ("Todos", "Everyone", "Público", "Public"):
            loc = page.get_by_text(label, exact=True)
            try:
                if loc.first.is_visible(timeout=1200):
                    loc.first.click(timeout=8000)
                    time.sleep(1)
                    return True
            except Exception:
                pass

    text = page_text(page, 22000)
    if re.search(r"\bTodos\b|\bEveryone\b|Público|Public", text, re.I):
        return True
    if re.search(r"Seguidores|Followers|Somente você|Apenas você|Only you|Amigos|Friends", text, re.I):
        return False
    return None


def privacy_is_public_or_selectable(page):
    text = page_text(page, 20000)
    if re.search(r"Everyone|Todos|Público|Public", text, re.I):
        return True
    if re.search(r"Only you|Somente você|Apenas você|Friends|Amigos", text, re.I):
        return False
    return None


def wait_confirmation(page, previous_url, timeout_seconds=90):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if tw.challenge_detected(page) or HUMAN_RE.search(page_text(page, 12000)):
            raise RuntimeError("TikTok solicitou CAPTCHA/verificação após o envio.")
        text = page_text(page, 18000)
        if SUCCESS_RE.search(text):
            return True
        current = str(page.url)
        if current != previous_url and "upload" not in current.lower():
            return True
        time.sleep(2)
    return False


def main():
    if MODE not in {"probe", "publish"}:
        raise RuntimeError("ATD_PUBLISH_MODE precisa ser probe ou publish.")

    state = tw.storage_state()
    item = None
    reported = False
    local_path = None

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=os.getenv("TIKTOK_CHROMIUM_EXECUTABLE") or None,
            headless=True,
            args=["--disable-dev-shm-usage", "--no-sandbox"],
        )
        context = browser.new_context(
            storage_state=state,
            viewport={"width": 1440, "height": 1000},
            locale="pt-BR",
        )
        page = context.new_page()

        try:
            file_input = open_upload(page, context)
            screenshot(page, "tiktok-upload-page.png")

            if MODE == "probe":
                print("TIKTOK_WEB_PROBE=OK", flush=True)
                return

            item = pc.claim("tiktok", queue_id=QUEUE_ID, manual=True)
            if not item:
                print("TIKTOK_WEB_NO_ITEM", flush=True)
                return

            local_path = pc.download(item)
            file_input.set_input_files(str(local_path))
            post_button = wait_upload_ready(page)
            handle_auto_checks_modal(page)
            screenshot(page, "tiktok-upload-ready.png")

            privacy = set_public_visibility(page)
            if privacy is False:
                message = (
                    "A interface do TikTok não apresenta publicação pública para esta conta. "
                    "Abra a conta/publicação no TikTok e ajuste a privacidade antes de automatizar."
                )
                pc.finish(item, "needs_human", error=message)
                reported = True
                raise RuntimeError(message)

            post_button = enabled_post_button(page) or post_button
            before = str(page.url)
            post_button.click(timeout=30000)
            confirmed = wait_confirmation(page, before)
            screenshot(page, "tiktok-after-post.png")

            if not confirmed:
                message = (
                    "O clique em Publicar foi executado, porém a interface não exibiu confirmação "
                    "inequívoca. O item foi pausado para evitar publicação duplicada."
                )
                pc.finish(item, "needs_human", error=message)
                reported = True
                raise RuntimeError(message)

            pc.finish(item, "published", remote_id="")
            reported = True
            print(f"TIKTOK_WEB_PUBLISH=OK queue_id={item['queue_id']}", flush=True)

        except Exception as exc:
            screenshot(page, "tiktok-error.png")
            if item and not reported:
                text = str(exc)
                if re.search(r"captcha|verifica|sessão|login", text, re.I):
                    pc.finish(item, "needs_human", error=text)
                else:
                    pc.finish(item, "retry", error=text, retry_after=900)
                reported = True
            raise
        finally:
            context.close()
            browser.close()
            if local_path:
                try:
                    local_path.unlink(missing_ok=True)
                    local_path.parent.rmdir()
                except Exception:
                    pass


if __name__ == "__main__":
    print(f"Anthares TikTok Web Publisher {VERSION}; mode={MODE}", flush=True)
    try:
        main()
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr, flush=True)
        raise

# ui-fix-pending
