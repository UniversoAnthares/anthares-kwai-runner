import base64
import gzip
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "render-tiktok-worker"))

VERSION = "0.3.4"
# CI session diagnostic trigger 1
API = os.getenv("ANTHARES_VIDEO_ENDPOINT", "").rstrip("/")
SECRET = os.getenv("ANTHARES_VIDEO_SECRET", "")
MODE = os.getenv("ATD_MODE", "session").strip().lower()
STORAGE_RAW = os.getenv("TIKTOK_STORAGE_STATE", "").strip()
STORAGE_FILE = os.getenv("TIKTOK_STORAGE_STATE_FILE", "").strip()
# TIKTOK_STORAGE_STATE is canonical for remote executors (GitHub/Render).
# Keep the file form only as a local backwards-compatible fallback.
if not STORAGE_RAW and STORAGE_FILE:
    try:
        with open(STORAGE_FILE, "r", encoding="utf-8") as _fh:
            STORAGE_RAW = _fh.read().strip()
    except OSError as _exc:
        raise RuntimeError(f"Não foi possível ler TIKTOK_STORAGE_STATE_FILE: {_exc}") from _exc
EXPECTED_USERNAME = os.getenv("EXPECTED_TIKTOK_USERNAME", "lucasrosalem4").strip().lstrip("@").lower()
EXPECTED_USER_ID = os.getenv("EXPECTED_TIKTOK_USER_ID", "").strip()
RUN_ID = os.getenv("GITHUB_RUN_ID", f"local-{int(time.time() * 1000)}")
RUNNER = os.getenv("RUNNER_NAME", "github-hosted")
CONTROL_URL = os.getenv("ANTHARES_CONTROL_URL", "").rstrip("/")
CONTROL_TOKEN = os.getenv("ANTHARES_CONTROL_TOKEN", "")
AUTH_COOKIE_NAMES = {
    "sessionid", "sessionid_ss", "sid_tt", "sid_guard", "uid_tt", "uid_tt_ss"
}


def auth_cookie_names(state):
    cookies = state.get("cookies", []) if isinstance(state, dict) else []
    names = {
        str(cookie.get("name", "")).lower()
        for cookie in cookies
        if isinstance(cookie, dict)
    }
    return sorted(names & AUTH_COOKIE_NAMES)


def preflight():
    require_env()
    if MODE != "session":
        raise RuntimeError("Nesta etapa, apenas ATD_MODE=session esta liberado.")
    state = storage_state()
    auth = auth_cookie_names(state)
    if not auth:
        raise RuntimeError("Sessao sem cookies de autenticacao reconhecidos do TikTok.")
    print(f"Preflight OK; worker={VERSION}; cookiesAuth={len(auth)}", flush=True)
    return state

def main():
    state = preflight()
    completed = False
    heartbeat("starting")
    control_heartbeat("starting")
    cycle("start", "session-test iniciado")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright Python não está instalado.") from exc

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=["--disable-dev-shm-usage","--no-sandbox","--disable-gpu","--disable-extensions","--disable-background-networking","--disable-component-update","--disable-default-apps","--disable-sync","--no-first-run","--no-zygote","--renderer-process-limit=1"],
            )
            try:
                context = browser.new_context(
                    storage_state=state,
                    viewport={"width": 1280, "height": 900},
                    locale="pt-BR",
                )
                try:
                    page = context.new_page()
                    page.goto(
                        "https://www.tiktok.com/foryou",
                        wait_until="domcontentloaded",
                        timeout=60000,
                    )
                    time.sleep(5)
                    validate_tiktok_session(page, context)
                    try:
                        from render_session import persist_session_state
                        persisted = persist_session_state(context.storage_state())
                        if persisted:
                            print("TIKTOK_SESSION_PERSIST=OK", flush=True)
                        else:
                            print("TIKTOK_SESSION_PERSIST=UNAVAILABLE", flush=True)
                            if os.getenv("REQUIRE_CENTRAL_SESSION_PERSIST", "").strip() == "1":
                                raise RuntimeError("Persistencia central da sessao TikTok indisponivel")
                    except Exception as exc:
                        print(f"TIKTOK_SESSION_PERSIST=SKIPPED {type(exc).__name__}: {str(exc)[:300]}", flush=True)
                    completed = True
                finally:
                    context.close()
            finally:
                browser.close()
    except Exception as exc:
        try:
            cycle("error", str(exc)[:400])
        except Exception:
            pass
        control_heartbeat("failed", failures=1)
        raise
    finally:
        try:
            heartbeat("finished")
        except Exception:
            pass
        if completed:
            control_heartbeat("finished")


def require_env():
    missing = []
    if MODE != "session":
        if not API:
            missing.append("ANTHARES_VIDEO_ENDPOINT")
        if not SECRET:
            missing.append("ANTHARES_VIDEO_SECRET")
    if not STORAGE_RAW.strip():
        missing.append("TIKTOK_STORAGE_STATE")
    if missing:
        raise RuntimeError("Secrets ausentes: " + ", ".join(missing))

def api(path, method="GET", payload=None, timeout=45):
    headers = {"X-Anthares-Worker-Secret": SECRET}
    data = None
    if payload is not None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:400]
        raise RuntimeError(f"{path}: HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{path}: falha de conexão: {exc.reason}") from exc
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{path}: resposta do WordPress não é JSON.") from exc


def heartbeat(status):
    if not API or not SECRET:
        return {}
    return api(
        "/heartbeat",
        "POST",
        {
            "worker_id": "github-actions-tiktok",
            "runner": RUNNER,
            "version": VERSION,
            "mode": MODE,
            "status": status,
        },
    )


def control_heartbeat(status, failures=0):
    """Best-effort Cloudflare control-plane heartbeat.

    This deliberately stays optional while the executor is used locally. Both
    variables must be supplied by the host's secret store; source code never
    supplies a URL token or falls back to a development secret.
    """
    if not CONTROL_URL or not CONTROL_TOKEN:
        return None
    payload = {
        "executor": "github",
        "runner": RUNNER,
        "version": VERSION,
        "status": status,
        "healthy": status != "failed",
        "failures": int(failures),
    }
    request = urllib.request.Request(
        CONTROL_URL + "/heartbeat",
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={
            "X-Anthares-Executor-Key": hashlib.sha256((CONTROL_TOKEN + ":github").encode("utf-8")).hexdigest(),
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8", "replace") or "{}")
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError):
        print("Cloudflare control heartbeat indisponível.", file=sys.stderr, flush=True)
        return None


def cycle(event, message=""):
    if not API or not SECRET:
        return {}
    return api(
        "/cycle",
        "POST",
        {
            "event": event,
            "run_id": RUN_ID,
            "examined": 0,
            "eligible": 0,
            "uploaded": 0,
            "duplicates": 0,
            "message": message,
        },
    )


def decode_storage(raw):
    text = raw.strip()
    if not text:
        raise RuntimeError("TIKTOK_STORAGE_STATE está vazio.")

    candidates = [text]
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        candidates.insert(0, text[1:-1].strip())

    for candidate in candidates:
        if candidate.startswith(("{", "[")):
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

    encoded = re.sub(r"\s+", "", candidates[0])
    encoded += "=" * ((4 - len(encoded) % 4) % 4)
    errors = []
    for decoder in (base64.b64decode, base64.urlsafe_b64decode):
        try:
            packed = decoder(encoded)
            try:
                return json.loads(gzip.decompress(packed).decode("utf-8"))
            except (gzip.BadGzipFile, OSError):
                return json.loads(packed.decode("utf-8"))
        except Exception as exc:
            errors.append(type(exc).__name__)

    raise RuntimeError(
        "TIKTOK_STORAGE_STATE não é JSON nem gzip+base64 válido "
        f"(tamanho={len(text)}; tentativas={','.join(errors)})."
    )


def storage_state():
    state = decode_storage(STORAGE_RAW)
    if isinstance(state, list):
        state = {"cookies": state, "origins": []}
    if not isinstance(state, dict):
        raise RuntimeError("TIKTOK_STORAGE_STATE precisa ser um objeto JSON ou uma lista de cookies.")
    cookies = state.get("cookies")
    if not isinstance(cookies, list) or not cookies:
        raise RuntimeError("TIKTOK_STORAGE_STATE não contém cookies.")
    clean_cookies = []
    for cookie in cookies:
        if not isinstance(cookie, dict) or not cookie.get("name") or not cookie.get("domain"):
            continue
        normalized = dict(cookie)
        if "expirationDate" in normalized and "expires" not in normalized:
            normalized["expires"] = normalized.pop("expirationDate")
        same_site = normalized.get("sameSite")
        if same_site in ("strict", "lax", "none"):
            normalized["sameSite"] = same_site.capitalize()
        elif same_site not in ("Strict", "Lax", "None"):
            normalized["sameSite"] = "Lax"
        clean_cookies.append(normalized)
    if not clean_cookies:
        raise RuntimeError("TIKTOK_STORAGE_STATE não contém cookies utilizáveis.")
    origins = state.get("origins", [])
    if not isinstance(origins, list):
        origins = []
    return {"cookies": clean_cookies, "origins": origins}


def challenge_detected(page):
    try:
        title = page.title()
    except Exception:
        title = ""
    try:
        body = page.locator("body").inner_text(timeout=3000)[:12000]
    except Exception:
        body = ""
    try:
        url = str(page.url).lower()
    except Exception:
        url = ""
    text = title + "\n" + body
    pattern = re.compile(
        r"captcha|verify to continue|security check|unusual traffic|"
        r"verifique para continuar|confirme que você",
        re.I,
    )
    return bool(pattern.search(text) or "/captcha" in url or "/challenge" in url)


def login_visible(page):
    selectors = (
        '[data-e2e="top-login-button"]',
        'button:has-text("Entrar")',
        'button:has-text("Log in")',
    )
    for selector in selectors:
        try:
            if page.locator(selector).first.is_visible(timeout=1200):
                return True
        except Exception:
            pass
    return False


def validate_tiktok_session(page, context):
    title = page.title()
    fast_session = os.getenv("ATD_FAST_SESSION", "").strip() == "1"
    if challenge_detected(page):
        raise RuntimeError("TikTok apresentou CAPTCHA/verificação ao runner do GitHub.")

    cookies = context.cookies("https://www.tiktok.com")
    auth = auth_cookie_names({"cookies": cookies})
    login = login_visible(page)
    authenticated = bool(auth) and not login
    if EXPECTED_USERNAME:
        expected = EXPECTED_USERNAME.lower()
        found = set()
        try:
            raw = page.locator('#__UNIVERSAL_DATA_FOR_REHYDRATION__').text_content(timeout=5000)
            data = json.loads(raw or '{}')
            current_user = (
                data.get('__DEFAULT_SCOPE__', {})
                .get('webapp.app-context', {})
                .get('user', {})
            )
            unique_id = str(current_user.get('uniqueId', '')).strip().lower()
            if unique_id:
                found.add(unique_id)
        except Exception:
            pass
        try:
            hrefs = page.locator('a[href*="/@"]').evaluate_all("(els)=>els.map(e=>e.href)")
            for href in hrefs:
                match = re.search(r"tiktok\.com/@([^/?#]+)", str(href), re.I)
                if match:
                    found.add(match.group(1).lower())
        except Exception:
            pass
        if expected not in found and not fast_session:
            try:
                page.goto("https://www.tiktok.com/profile", wait_until="domcontentloaded", timeout=30000)
                time.sleep(2)
                match = re.search(r"tiktok\.com/@([^/?#]+)", str(page.url), re.I)
                if match:
                    found.add(match.group(1).lower())
                hrefs = page.locator('a[href*="/@"]').evaluate_all("(els)=>els.map(e=>e.href)")
                for href in hrefs:
                    match = re.search(r"tiktok\.com/@([^/?#]+)", str(href), re.I)
                    if match:
                        found.add(match.group(1).lower())
            except Exception:
                pass
        if expected not in found and not fast_session:
            for identity_url in (
                "https://www.tiktok.com/tiktokstudio",
                "https://www.tiktok.com/tiktokstudio/upload?from=webapp",
                "https://www.tiktok.com/upload?lang=pt-BR",
            ):
                try:
                    page.goto(identity_url, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(2)
                    match = re.search(r"tiktok\.com/@([^/?#]+)", str(page.url), re.I)
                    if match:
                        found.add(match.group(1).lower())
                    hrefs = page.locator('a[href*="/@"]').evaluate_all("(els)=>els.map(e=>e.href)")
                    for href in hrefs:
                        match = re.search(r"tiktok\.com/@([^/?#]+)", str(href), re.I)
                        if match:
                            found.add(match.group(1).lower())
                    if expected in found:
                        break
                except Exception:
                    pass
        if expected not in found and not fast_session:
            try:
                profile = page.request.get("https://www.tiktok.com/profile", timeout=30000)
                match = re.search(r'tiktok\.com/@([^/?#"\\]+)', profile.text(), re.I)
                if match:
                    found.add(match.group(1).lower())
            except Exception:
                pass
        if expected not in found and EXPECTED_USER_ID:
            try:
                multi = next(
                    (cookie.get("value", "") for cookie in cookies if cookie.get("name") == "multi_sids"),
                    "",
                )
                decoded = urllib.parse.unquote(str(multi))
                account_ids = {part.split(":", 1)[0] for part in decoded.split(",") if ":" in part}
                if EXPECTED_USER_ID in account_ids:
                    found.add(expected)
            except Exception:
                pass
        print("TIKTOK_ACCOUNT_CANDIDATES=" + json.dumps(sorted(found), ensure_ascii=False), flush=True)
        if expected not in found:
            cycle("error", "Conta TikTok esperada nao confirmada por link de perfil.")
            raise RuntimeError("Conta TikTok esperada nao confirmada; publicacao bloqueada.")
    message = (
        f"session-test; authenticated={str(authenticated).lower()}; "
        f"title={title}; loginVisible={str(login).lower()}; authCookies={len(auth)}"
    )
    print(message, flush=True)

    if not authenticated:
        cycle("error", message)
        raise RuntimeError("Sessão TikTok não autenticada ou expirada.")

    heartbeat("online")
    cycle("finish", message)
    print("Sessão TikTok autenticada.", flush=True)


def inventory_profile_videos(username=None):
    """Read-only inventory using DOM plus TikTok hydration/network payloads."""
    target=(username or EXPECTED_USERNAME or "").strip().lstrip("@")
    if not target:
        raise RuntimeError("Conta TikTok alvo ausente.")
    from playwright.sync_api import sync_playwright
    seen={}

    def add_video(video_id, desc=""):
        video_id=str(video_id or "").strip()
        if not re.fullmatch(r"\\d{10,}",video_id):
            return
        item=seen.setdefault(video_id,{
            "id":video_id,
            "url":f"https://www.tiktok.com/@{target}/video/{video_id}",
            "text":"",
        })
        if desc and not item["text"]:
            item["text"]=" ".join(str(desc).split())[:500]

    def walk(value):
        if isinstance(value,dict):
            vid=value.get("id") or value.get("aweme_id")
            desc=value.get("desc") or value.get("description") or value.get("title") or ""
            if vid:
                add_video(vid,desc)
            for child in value.values():
                walk(child)
        elif isinstance(value,list):
            for child in value:
                walk(child)

    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--disable-dev-shm-usage","--no-sandbox","--disable-gpu","--disable-extensions","--disable-background-networking","--disable-component-update","--disable-default-apps","--disable-sync","--no-first-run","--no-zygote","--renderer-process-limit=1"])
        context=browser.new_context(storage_state=storage_state(),viewport={"width":1440,"height":1000},locale="pt-BR")
        page=context.new_page()

        def inspect_response(response):
            try:
                url=str(response.url)
                if not any(token in url for token in ("/api/post/item_list/","/api/recommend/item_list/","item_list")):
                    return
                if "application/json" not in str(response.headers.get("content-type","")).lower():
                    return
                walk(response.json())
            except Exception:
                pass

        page.on("response",inspect_response)
        try:
            page.goto(f"https://www.tiktok.com/@{target}",wait_until="domcontentloaded",timeout=60000)
            time.sleep(8)
            if challenge_detected(page):
                raise RuntimeError("TikTok apresentou CAPTCHA/verificação no inventário.")
            cookies=context.cookies("https://www.tiktok.com")
            if not auth_cookie_names({"cookies":cookies}) or login_visible(page):
                raise RuntimeError("Sessão TikTok não autenticada para inventário.")

            sec_uid=""
            for selector in ("#__UNIVERSAL_DATA_FOR_REHYDRATION__","#SIGI_STATE"):
                try:
                    raw=page.locator(selector).text_content(timeout=2500)
                    if raw:
                        hydration=json.loads(raw)
                        walk(hydration)
                        match=re.search(r'"secUid"\\s*:\\s*"([^"]+)"',raw)
                        if match:
                            sec_uid=match.group(1)
                except Exception:
                    pass

            # O perfil pode anunciar videoCount mas entregar itemList vazio na hidratação.
            # Nesse caso consultamos a mesma listagem de posts usada pela página, com
            # a sessão do contexto e o secUid obtido do próprio perfil.
            if sec_uid and not seen:
                try:
                    api_url=(
                        "https://www.tiktok.com/api/post/item_list/"
                        "?WebIdLastTime=0&aid=1988&app_language=pt-BR&app_name=tiktok_web"
                        "&browser_language=pt-BR&browser_name=Mozilla&browser_online=true"
                        "&count=35&cursor=0&device_platform=web_pc&focus_state=true"
                        "&from_page=user&history_len=2&is_fullscreen=false"
                        "&is_page_visible=true&os=windows&priority_region=BR"
                        "&referer=&region=BR&screen_height=1000&screen_width=1440"
                        "&tz_name=America%2FCampo_Grande&user_is_login=true"
                        "&secUid="+urllib.parse.quote(sec_uid,safe="")
                    )
                    response=page.request.get(api_url,timeout=30000,headers={
                        "Referer":f"https://www.tiktok.com/@{target}",
                    })
                    if response.ok:
                        walk(response.json())
                    else:
                        print("TIKTOK_PROFILE_API_STATUS="+str(response.status),flush=True)
                except Exception as exc:
                    print("TIKTOK_PROFILE_API_ERROR="+type(exc).__name__,flush=True)

            try:
                links=page.locator('a[href*="/video/"]').evaluate_all(
                    "(els)=>els.map(e=>({href:e.href,text:(e.innerText||e.getAttribute('aria-label')||'').trim()}))"
                )
                for item in links:
                    match=re.search(r"/video/(\\d+)",str(item.get("href") or ""))
                    if match:
                        add_video(match.group(1),item.get("text") or "")
            except Exception:
                pass

            for _ in range(3):
                page.mouse.wheel(0,1800)
                time.sleep(2)

            videos=list(seen.values())
            print("TIKTOK_PROFILE_VIDEO_COUNT="+str(len(videos)),flush=True)
            for index,item in enumerate(videos,1):
                print(f"TIKTOK_PROFILE_VIDEO_{index}_ID="+item["id"],flush=True)
                print(f"TIKTOK_PROFILE_VIDEO_{index}_URL="+item["url"],flush=True)
                safe_text=re.sub(r"[\\r\\n]+"," ",item["text"]).strip()
                print(f"TIKTOK_PROFILE_VIDEO_{index}_TEXT="+safe_text,flush=True)
            return videos
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    print(f"Anthares TikTok Worker {VERSION}; modo={MODE}", flush=True)
    try:
        main()
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr, flush=True)
        raise
