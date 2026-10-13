import asyncio
import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from threading import Lock
from typing import Any

import psutil
import websocket
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Anthares-browser control API", version="0.2.1")
PROFILE_DIR = Path(os.environ.get("CHROME_PROFILE_DIR", "/data/chrome-profile"))
CONTROL_TOKEN = os.environ.get("CONTROL_TOKEN", "")
CDP_PORT = int(os.environ.get("CDP_PORT", "9222"))
CDP_HTTP = f"http://127.0.0.1:{CDP_PORT}"
_BROWSER_LOCK = Lock()


class NavigateRequest(BaseModel):
    url: str
    wait_ms: int = Field(default=1200, ge=0, le=30000)


class SelectorRequest(BaseModel):
    selector: str
    wait_ms: int = Field(default=1000, ge=0, le=30000)


class TypeRequest(BaseModel):
    selector: str
    text: str
    clear: bool = True
    wait_ms: int = Field(default=250, ge=0, le=30000)


class EvaluateRequest(BaseModel):
    expression: str
    return_by_value: bool = True


class WaitRequest(BaseModel):
    selector: str
    timeout_ms: int = Field(default=10000, ge=100, le=120000)
    visible: bool = True


def require_token(authorization: str | None = Header(default=None)) -> None:
    if not CONTROL_TOKEN:
        raise HTTPException(status_code=503, detail="CONTROL_TOKEN not configured")
    if authorization != f"Bearer {CONTROL_TOKEN}":
        raise HTTPException(status_code=401, detail="unauthorized")


def chromium_processes() -> list[int]:
    pids: list[int] = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = (proc.info.get("name") or "").lower()
            cmd = " ".join(proc.info.get("cmdline") or []).lower()
            if "chromium" in name or "chromium" in cmd or "chrome" in name:
                pids.append(int(proc.info["pid"]))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return sorted(set(pids))


def _json_get(path: str) -> Any:
    try:
        with urllib.request.urlopen(f"{CDP_HTTP}{path}", timeout=2) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=503, detail=f"CDP unavailable: {exc}") from exc


def _page_target() -> dict[str, Any]:
    targets = _json_get("/json/list")
    for target in targets:
        if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
            return target
    raise HTTPException(status_code=503, detail="No Chromium page target available")


def _cdp_ready() -> bool:
    try:
        _page_target()
        return True
    except HTTPException:
        return False


def _cdp_call(method: str, params: dict[str, Any] | None = None, timeout: float = 10.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_exc: Exception | None = None
    while time.monotonic() < deadline:
        try:
            target = _page_target()
            ws = websocket.create_connection(
                target["webSocketDebuggerUrl"],
                timeout=min(2.0, max(0.2, deadline - time.monotonic())),
                suppress_origin=True,
            )
            break
        except Exception as exc:
            last_exc = exc
            time.sleep(0.1)
    else:
        raise HTTPException(status_code=503, detail=f"CDP websocket unavailable after retry: {last_exc}") from last_exc

    request_id = int(time.time_ns() % 2_000_000_000)
    try:
        ws.send(json.dumps({"id": request_id, "method": method, "params": params or {}}))
        while time.monotonic() < deadline:
            ws.settimeout(max(0.2, deadline - time.monotonic()))
            message = json.loads(ws.recv())
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise HTTPException(status_code=502, detail={"cdp_error": message["error"], "method": method})
            return message.get("result", {})
        raise HTTPException(status_code=504, detail=f"CDP timeout: {method}")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"CDP command failed: {exc}") from exc
    finally:
        try:
            ws.close()
        except Exception:
            pass


def _evaluate(expression: str, return_by_value: bool = True) -> dict[str, Any]:
    result = _cdp_call(
        "Runtime.evaluate",
        {
            "expression": expression,
            "awaitPromise": True,
            "returnByValue": return_by_value,
            "userGesture": True,
        },
    )
    if result.get("exceptionDetails"):
        details = result["exceptionDetails"]
        raise HTTPException(status_code=422, detail={"javascript_exception": details})
    return result.get("result", {})


def _js_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _validate_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=422, detail="Only absolute http/https URLs are allowed")
    return url


def _sleep_ms(wait_ms: int) -> None:
    if wait_ms:
        time.sleep(wait_ms / 1000)


def _profile_size() -> int:
    size = 0
    if PROFILE_DIR.exists():
        for path in PROFILE_DIR.rglob("*"):
            try:
                if path.is_file():
                    size += path.stat().st_size
            except OSError:
                pass
    return size


@app.get("/health")
def health() -> dict[str, Any]:
    """Liveness only; use /ready for real browser readiness."""
    return {"ok": True, "service": "anthares-browser", "readiness_path": "/ready"}


@app.get("/ready")
def ready() -> dict[str, Any]:
    """Fail closed if the browser or persistent-profile mount is unavailable."""
    profile_exists = PROFILE_DIR.is_dir()
    browser_running = bool(chromium_processes())
    cdp_ready = _cdp_ready() if browser_running else False
    evidence = {
        "ok": profile_exists and browser_running and cdp_ready,
        "profile_dir_exists": profile_exists,
        "chromium_running": browser_running,
        "cdp_ready": cdp_ready,
    }
    if not evidence["ok"]:
        raise HTTPException(status_code=503, detail=evidence)
    return evidence


@app.get("/status")
def status(_: None = Depends(require_token)) -> dict[str, Any]:
    return {
        "profile_dir": str(PROFILE_DIR),
        "profile_dir_exists": PROFILE_DIR.exists(),
        "profile_bytes": _profile_size(),
        "chromium_pids": chromium_processes(),
        "cdp_ready": _cdp_ready(),
        "cdp_bind": "127.0.0.1",
        "cdp_port": CDP_PORT,
        "session_claim": "not_verified",
    }


@app.get("/page")
def page(_: None = Depends(require_token)) -> dict[str, Any]:
    with _BROWSER_LOCK:
        data = _evaluate(
            "(() => ({url: location.href, title: document.title, text: (document.body?.innerText || '').slice(0, 50000)}))()"
        ).get("value", {})
        return data


@app.post("/navigate")
def navigate(req: NavigateRequest, _: None = Depends(require_token)) -> dict[str, Any]:
    with _BROWSER_LOCK:
        _cdp_call("Page.navigate", {"url": _validate_url(req.url)})
        _sleep_ms(req.wait_ms)
        return page_state_unlocked()


def page_state_unlocked() -> dict[str, Any]:
    return _evaluate(
        "(() => ({url: location.href, title: document.title, text: (document.body?.innerText || '').slice(0, 50000)}))()"
    ).get("value", {})


@app.post("/click")
def click(req: SelectorRequest, _: None = Depends(require_token)) -> dict[str, Any]:
    with _BROWSER_LOCK:
        selector = _js_string(req.selector)
        _evaluate(
            f"""(() => {{
                const el = document.querySelector({selector});
                if (!el) throw new Error('selector not found: ' + {selector});
                el.scrollIntoView({{block:'center', inline:'center'}});
                el.click();
                return true;
            }})()"""
        )
        _sleep_ms(req.wait_ms)
        return page_state_unlocked()


@app.post("/type")
def type_text(req: TypeRequest, _: None = Depends(require_token)) -> dict[str, Any]:
    with _BROWSER_LOCK:
        selector = _js_string(req.selector)
        clear = "true" if req.clear else "false"
        _evaluate(
            f"""(() => {{
                const el = document.querySelector({selector});
                if (!el) throw new Error('selector not found: ' + {selector});
                el.scrollIntoView({{block:'center', inline:'center'}});
                el.focus();
                if ({clear}) {{
                    if ('value' in el) el.value = '';
                    else el.textContent = '';
                    el.dispatchEvent(new Event('input', {{bubbles:true}}));
                }}
                return true;
            }})()"""
        )
        _cdp_call("Input.insertText", {"text": req.text})
        _sleep_ms(req.wait_ms)
        return {"ok": True, "selector": req.selector, "chars": len(req.text), "page": page_state_unlocked()}


@app.post("/wait")
def wait_for_selector(req: WaitRequest, _: None = Depends(require_token)) -> dict[str, Any]:
    deadline = time.monotonic() + (req.timeout_ms / 1000)
    selector = _js_string(req.selector)
    with _BROWSER_LOCK:
        while time.monotonic() < deadline:
            expression = f"""(() => {{
                const el = document.querySelector({selector});
                if (!el) return false;
                if (!{str(req.visible).lower()}) return true;
                const s = getComputedStyle(el), r = el.getBoundingClientRect();
                return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0;
            }})()"""
            if _evaluate(expression).get("value") is True:
                return {"ok": True, "selector": req.selector}
            time.sleep(0.2)
    raise HTTPException(status_code=408, detail=f"selector timeout: {req.selector}")


@app.post("/evaluate")
def evaluate(req: EvaluateRequest, _: None = Depends(require_token)) -> dict[str, Any]:
    with _BROWSER_LOCK:
        result = _evaluate(req.expression, req.return_by_value)
        return {"result": result}


@app.get("/screenshot")
def screenshot(_: None = Depends(require_token)) -> dict[str, Any]:
    with _BROWSER_LOCK:
        result = _cdp_call("Page.captureScreenshot", {"format": "png", "fromSurface": True}, timeout=20.0)
        data = result.get("data", "")
        if not data:
            raise HTTPException(status_code=502, detail="Chromium returned an empty screenshot")
        try:
            base64.b64decode(data, validate=True)
        except ValueError as exc:
            raise HTTPException(status_code=502, detail="Invalid screenshot payload") from exc
        return {"format": "png", "base64": data}


@app.get("/targets")
def targets(_: None = Depends(require_token)) -> list[dict[str, Any]]:
    with _BROWSER_LOCK:
        return [
            {
                "id": target.get("id"),
                "type": target.get("type"),
                "title": target.get("title"),
                "url": target.get("url"),
            }
            for target in _json_get("/json/list")
        ]


@app.get("/session/evidence")
def session_evidence(_: None = Depends(require_token)) -> dict[str, Any]:
    """Conservative service-specific evidence; never infer login from cookies."""
    with _BROWSER_LOCK:
        data = _evaluate("""(() => {
            const host = location.hostname.toLowerCase();
            if (host !== 'kwai.com' && !host.endsWith('.kwai.com'))
                return {state:'unknown', reason:'not_kwai'};
            const body = (document.body?.innerText || '').slice(0, 12000).toLowerCase();
            const dialog = Array.from(document.querySelectorAll('[role="dialog"],[aria-modal="true"]'))
                .some(el => /log in|sign in|login|entrar|fazer login|登录/i.test(el.innerText || ''));
            const explicit = dialog || /please log in|please sign in|faça login para|entre na sua conta/.test(body);
            return explicit
                ? {state:'unauthenticated', reason:'visible_login_prompt'}
                : {state:'unknown', reason:'authentication_not_proven'};
        })()""").get("value", {})
        if not isinstance(data, dict) or data.get("state") not in {"unknown", "unauthenticated"}:
            return {"state": "unknown", "reason": "invalid_evidence"}
        return data
