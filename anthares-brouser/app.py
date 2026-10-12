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

app = FastAPI(title="Anthares-browser control API", version="0.2.0")
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
    target = _page_target()
    ws_url = target["webSocketDebuggerUrl"]
    request_id = int(time.time_ns() % 2_000_000_000)
    try:
        ws = websocket.create_connection(
            ws_url,
            timeout=timeout,
            origin=f"http://127.0.0.1:{CDP_PORT}",
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"CDP websocket unavailable: {exc}") from exc
    try:
        ws.send(json.dumps({"id": request_id, "method": method, "params": params or {}}))
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
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
    return {
        "ok": True,
        "profile_dir_exists": PROFILE_DIR.exists(),
        "chromium_running": bool(chromium_processes()),
        "cdp_ready": _cdp_ready(),
    }


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
        # Validate the payload before returning it; do not persist screenshots to the profile volume.
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
