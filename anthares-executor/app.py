import asyncio
import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright

CDP_PORT = int(os.getenv("CDP_PORT", "9222"))
CDP_URL = f"http://127.0.0.1:{CDP_PORT}"
TOKEN = os.getenv("ANTHARES_EXECUTOR_TOKEN", "")
EXPECTED_ACCOUNT = os.getenv("KWAI_EXPECTED_ACCOUNT", "lucasrosalem").lstrip("@").lower()
HANDLE_RE = re.compile(r"^[A-Za-z0-9._-]{1,40}$")
STATE_FILE = Path(os.getenv("ANTHARES_STATE_FILE", "/run/anthares-executor/state.json"))

app = FastAPI(title="Anthares Executor", docs_url=None, redoc_url=None)
probe_lock = asyncio.Lock()
seen_jobs: dict[str, dict[str, Any]] = {}
highest_generation: dict[str, int] = {}


class ProbeRequest(BaseModel):
    job_id: str = Field(min_length=8, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")
    generation: int = Field(ge=1)
    handle: str = Field(default=EXPECTED_ACCOUNT, min_length=1, max_length=40)


def require_auth(authorization: str | None) -> None:
    if not TOKEN:
        raise HTTPException(503, "executor_not_configured")
    supplied = (authorization or "").removeprefix("Bearer ")
    import hmac
    if not hmac.compare_digest(supplied, TOKEN):
        raise HTTPException(401, "unauthorized")


def cdp_ready() -> bool:
    try:
        with urllib.request.urlopen(CDP_URL + "/json/version", timeout=1.5) as r:
            return r.status == 200
    except Exception:
        return False


def restored_state() -> dict[str, Any]:
    try:
        value = json.loads(STATE_FILE.read_text())
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


@app.get("/health")
def health():
    return {"ok": True, "service": "anthares-executor"}


@app.get("/ready")
def ready():
    if not cdp_ready():
        raise HTTPException(503, "chromium_not_ready")
    return {"ok": True, "chromium": True, "state": restored_state()}


@app.get("/v1/capabilities")
def capabilities(authorization: str | None = Header(default=None)):
    require_auth(authorization)
    return {
        "ok": True,
        "provider": "anthares-executor",
        "operations": ["kwai.readonly_probe"],
        "max_concurrency": 1,
        "publishing_enabled": False,
        "profile_backend": "gitlab_encrypted_snapshot",
    }


async def inspect_profile(page, handle: str) -> dict[str, Any]:
    await page.goto(f"https://www.kwai.com/@{handle}", wait_until="domcontentloaded", timeout=18000)
    await page.wait_for_timeout(1200)
    return await page.evaluate("""([expected]) => {
      const visible = el => { const r=el.getBoundingClientRect(),s=getComputedStyle(el); return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'; };
      const txt = el => ((el.innerText||el.textContent||'')+' '+(el.getAttribute?.('aria-label')||'')).replace(/\\s+/g,' ').trim();
      const nodes=[...document.querySelectorAll('a[href],button,[role="button"],[role="menuitem"],input,span,div')];
      const login=nodes.some(el=>visible(el)&&(/^(log\\s*in|login|sign\\s*in|entrar|fazer login)$/i.test(txt(el))||['password','tel'].includes((el.getAttribute?.('type')||'').toLowerCase())));
      const owner=nodes.some(el=>visible(el)&&(/^(edit profile|editar perfil|account settings|configura[cç][oõ]es da conta)$/i.test(txt(el))||/edit[-_ ]?profile|profile[-_ ]?edit/i.test(el.getAttribute?.('data-testid')||'')||/\\/(profile|account)\\/(edit|settings)(\\/|$)/i.test(el.getAttribute?.('href')||'')));
      return {host:location.hostname.toLowerCase(),path:location.pathname.replace(/\\/$/,'').toLowerCase(),login_gate:login,owner_edit:owner,expected};
    }""", [handle.lower()])


async def inspect_studio(page) -> dict[str, Any]:
    await page.goto("https://studio.kwai.com/", wait_until="domcontentloaded", timeout=18000)
    await page.wait_for_timeout(1200)
    return await page.evaluate("""() => {
      const body=(document.body?.innerText||'').slice(0,24000);
      const login=!!document.querySelector('input[type="password"],input[type="tel"]')||/(^|\\n)\\s*(log\\s*in|login|sign\\s*in|entrar|fazer login)\\s*($|\\n)/i.test(body);
      const file=!!document.querySelector('input[type="file"]:not([disabled])');
      const upload=/upload|enviar|carregar|create video|criar v[ií]deo|new post|novo post/i.test(body);
      return {host:location.hostname.toLowerCase(),login_gate:login,file_input:file,upload_control:upload};
    }""")


async def run_probe(handle: str) -> dict[str, Any]:
    if not cdp_ready():
        return {"ok": False, "error": "chromium_not_ready", "identity_verified": False, "upload_surface_verified": False}
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(CDP_URL)
        try:
            context = browser.contexts[0]
            pages = context.pages
            page = pages[0] if pages else await context.new_page()
            await page.route(re.compile(r".*\\.(png|jpe?g|gif|webp|avif|mp4|webm|mp3|woff2?|ttf)(\\?.*)?$", re.I), lambda route: route.abort())
            profile = await inspect_profile(page, handle)
            exact = profile.get("host") == "www.kwai.com" and profile.get("path") == "/@" + handle.lower()
            identity = bool(exact and profile.get("owner_edit") and not profile.get("login_gate"))
            studio = {"host_ok": False, "login_gate": False, "file_input": False, "upload_control": False}
            if identity:
                raw = await inspect_studio(page)
                studio = {
                    "host_ok": raw.get("host") == "studio.kwai.com",
                    "login_gate": bool(raw.get("login_gate")),
                    "file_input": bool(raw.get("file_input")),
                    "upload_control": bool(raw.get("upload_control")),
                }
            upload = bool(identity and studio["host_ok"] and not studio["login_gate"] and (studio["file_input"] or studio["upload_control"]))
            return {
                "ok": True,
                "identity_verified": identity,
                "upload_surface_verified": upload,
                "session_state": "authenticated" if identity else ("unauthenticated" if profile.get("login_gate") else "unknown"),
                "profile": {"exact_route": exact, "owner_edit": bool(profile.get("owner_edit")), "login_gate": bool(profile.get("login_gate"))},
                "studio": studio,
            }
        finally:
            try:
                for p in browser.contexts[0].pages:
                    await p.goto("about:blank", wait_until="commit", timeout=3000)
            except Exception:
                pass
            await browser.close()


@app.post("/v1/probe")
async def probe(req: ProbeRequest, authorization: str | None = Header(default=None)):
    require_auth(authorization)
    handle = req.handle.lstrip("@").lower()
    if not HANDLE_RE.fullmatch(handle):
        raise HTTPException(400, "invalid_handle")
    cached = seen_jobs.get(req.job_id)
    if cached is not None:
        return cached
    prior = highest_generation.get(handle, 0)
    if req.generation < prior:
        raise HTTPException(409, "stale_generation")
    async with probe_lock:
        cached = seen_jobs.get(req.job_id)
        if cached is not None:
            return cached
        prior = highest_generation.get(handle, 0)
        if req.generation < prior:
            raise HTTPException(409, "stale_generation")
        highest_generation[handle] = req.generation
        try:
            result = await asyncio.wait_for(run_probe(handle), timeout=48)
        except asyncio.TimeoutError:
            result = {"ok": False, "error": "probe_timeout", "identity_verified": False, "upload_surface_verified": False}
        result.update({"job_id": req.job_id, "generation": req.generation, "read_only": True})
        seen_jobs[req.job_id] = result
        if len(seen_jobs) > 256:
            seen_jobs.pop(next(iter(seen_jobs)))
        return result
