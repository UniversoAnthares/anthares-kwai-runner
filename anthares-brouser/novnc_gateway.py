"""Authenticated same-origin gateway for loopback-only noVNC (no public VNC/CDP)."""
import asyncio
import base64
import hashlib
import hmac
import os
import secrets
import time
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response, WebSocket
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from starlette.websockets import WebSocketDisconnect

router = APIRouter()
COOKIE_NAME = "anthares_novnc_session"
SESSION_SECONDS = 43200
NOVNC_ROOT = Path(os.environ.get("NOVNC_STATIC_ROOT", "/usr/share/novnc"))
VNC_HOST = os.environ.get("NOVNC_VNC_HOST", "127.0.0.1")
VNC_PORT = int(os.environ.get("NOVNC_VNC_PORT", "5900"))
REVOKED = set()
MANUAL_TOKEN = os.environ.get("NOVNC_MANUAL_TOKEN", "")
try:
    MANUAL_EXPIRES = int(os.environ.get("NOVNC_MANUAL_EXPIRES", "0") or "0")
except ValueError:
    MANUAL_EXPIRES = 0
MANUAL_USED = False


def _secret() -> bytes:
    value = os.environ.get("CONTROL_TOKEN", "")
    if len(value) < 24:
        raise HTTPException(status_code=503, detail="CONTROL_TOKEN must be configured securely")
    return value.encode("utf-8")


def _authenticate(authorization: str | None = Header(default=None)) -> None:
    key = _secret()
    supplied = (authorization or "").encode("utf-8")
    if not supplied.startswith(b"Bearer ") or not hmac.compare_digest(supplied[7:], key):
        raise HTTPException(status_code=401, detail="unauthorized")


def _issue() -> str:
    exp = int(time.time()) + SESSION_SECONDS
    payload = f"{exp}:{secrets.token_hex(16)}"
    sig = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}:{sig}".encode()).decode().rstrip("=")


def _expiry(token: str | None) -> int:
    if not token or token in REVOKED:
        return 0
    try:
        decoded = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4)).decode()
        exp, nonce, sig = decoded.split(":")
        if len(nonce) != 32 or len(sig) != 64:
            return 0
        payload = f"{exp}:{nonce}"
        expected = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            return 0
        expiry = int(exp)
        return expiry if expiry > int(time.time()) else 0
    except (ValueError, UnicodeError, HTTPException):
        return 0


def _require_cookie(anthares_novnc_session: str | None = Cookie(default=None)) -> int:
    expiry = _expiry(anthares_novnc_session)
    if not expiry:
        raise HTTPException(status_code=401, detail="noVNC session expired or missing")
    return expiry


def _secure_cookie() -> bool:
    return os.environ.get("NOVNC_COOKIE_SECURE", "1") != "0"


def _set_session_cookie(response: Response) -> None:
    response.set_cookie(
        COOKIE_NAME, _issue(), max_age=SESSION_SECONDS, httponly=True,
        secure=_secure_cookie(), samesite="lax", path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"


@router.get("/novnc/login", response_class=HTMLResponse)
def login_form() -> HTMLResponse:
    html = ("<!doctype html><html lang='pt-BR'><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>Anthares Browser</title>"
            "<form action='/novnc/login' method='post'>"
            "<label>Chave de acesso <input name='access_token' type='password' "
            "required autocomplete='off' maxlength='512'></label>"
            "<button type='submit'>Abrir navegador remoto</button></form></html>")
    return HTMLResponse(html, headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer", "X-Content-Type-Options": "nosniff"})


@router.get("/novnc/once/{token}")
def manual_once(token: str, request: Request):
    global MANUAL_USED
    if _secure_cookie() and request.url.scheme != "https":
        raise HTTPException(status_code=403, detail="HTTPS required")
    now = int(time.time())
    supplied = token.encode("utf-8", "strict")
    expected = MANUAL_TOKEN.encode("utf-8", "strict")
    if MANUAL_USED or not expected or MANUAL_EXPIRES <= now or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=410, detail="manual access link expired or consumed")
    MANUAL_USED = True
    response = RedirectResponse(url="/novnc/vnc.html?path=novnc%2Fwebsockify", status_code=303)
    _set_session_cookie(response)
    return response


@router.post("/novnc/login")
async def browser_login(request: Request):
    if _secure_cookie() and request.url.scheme != "https":
        raise HTTPException(status_code=403, detail="HTTPS required")
    if request.headers.get("content-type", "").split(";")[0].strip() != "application/x-www-form-urlencoded":
        raise HTTPException(status_code=415, detail="unsupported form")
    raw = await request.body()
    if len(raw) > 1024:
        raise HTTPException(status_code=413, detail="form too large")
    params = parse_qs(raw.decode("utf-8", "replace"), keep_blank_values=True)
    supplied = params.get("access_token", [""])[0].encode("utf-8")
    if not hmac.compare_digest(supplied, _secret()):
        raise HTTPException(status_code=401, detail="unauthorized")
    response = RedirectResponse(url="/novnc/vnc.html?path=novnc%2Fwebsockify", status_code=303)
    _set_session_cookie(response)
    return response


@router.post("/novnc/session")
def create_session(response: Response, _: None = Depends(_authenticate)) -> dict:
    _set_session_cookie(response)
    return {"ok": True, "path": "/novnc/vnc.html", "expires_in_seconds": SESSION_SECONDS}


@router.post("/novnc/logout")
def revoke_session(
    response: Response,
    token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    _: None = Depends(_authenticate),
) -> dict:
    if token and _expiry(token):
        REVOKED.add(token)
    response.delete_cookie(COOKIE_NAME, path="/", secure=_secure_cookie(), httponly=True, samesite="lax")
    response.headers["Cache-Control"] = "no-store"
    return {"ok": True}


@router.get("/novnc")
def novnc_root(_: int = Depends(_require_cookie)):
    return RedirectResponse(url="/novnc/vnc.html?path=novnc%2Fwebsockify", status_code=303, headers={"Cache-Control": "no-store"})


@router.get("/novnc/{asset_path:path}")
def novnc_static(asset_path: str, _: int = Depends(_require_cookie)):
    root = NOVNC_ROOT.resolve()
    target = (root / asset_path).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(target, headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer"})


def _same_origin(websocket: WebSocket) -> bool:
    """Validate browser origin against the configured public HTTPS hostname.

    Render can rewrite the internal Host header while preserving the public
    browser Origin. Never trust arbitrary forwarded-host headers here.
    """
    origin = urlsplit(websocket.headers.get("origin", ""))
    public_url = urlsplit(os.environ.get(
        "NOVNC_PUBLIC_ORIGIN", "https://anthares-browser-qa-render.onrender.com"
    ))
    return bool(
        origin.scheme == "https"
        and origin.hostname == public_url.hostname
        and origin.port == public_url.port
        and public_url.scheme == "https"
    )


@router.websocket("/novnc/websockify")
async def novnc_websocket(websocket: WebSocket):
    """Bridge the authenticated browser websocket directly to loopback VNC TCP.

    noVNC already speaks raw RFB over websocket. A second websocket proxy layer
    is unnecessary and can stall RFB negotiation, so this endpoint terminates
    the public websocket itself and forwards bytes to x11vnc on 127.0.0.1:5900.
    """
    expiry = _expiry(websocket.cookies.get(COOKIE_NAME))
    print("[anthares-browser] ws auth cookie_present=%s valid=%s origin_valid=%s" % (
        bool(websocket.cookies.get(COOKIE_NAME)), bool(expiry), _same_origin(websocket)
    ), flush=True)
    if not expiry or not _same_origin(websocket):
        import logging
        logging.getLogger("anthares.novnc").warning(
            "websocket denied: cookie_present=%s cookie_valid=%s origin_valid=%s host=%s origin=%s",
            bool(websocket.cookies.get(COOKIE_NAME)), bool(expiry),
            _same_origin(websocket), websocket.headers.get("host", ""),
            websocket.headers.get("origin", ""),
        )
        await websocket.close(code=1008)
        return

    offered = [s.strip() for s in websocket.headers.get("sec-websocket-protocol", "").split(",") if s.strip()]
    selected = "binary" if "binary" in offered else ("base64" if "base64" in offered else None)
    writer = None
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(VNC_HOST, VNC_PORT), timeout=5)
        # x11vnc must send its 12-byte RFB greeting first. Verify the actual
        # TCP banner before upgrading the browser socket; preserve all bytes.
        banner = await asyncio.wait_for(reader.readexactly(12), timeout=12)
        if not banner.startswith(b"RFB "):
            raise RuntimeError("VNC endpoint returned an invalid RFB greeting")
        await websocket.accept(subprotocol=selected)
        if selected == "base64":
            await websocket.send_text(base64.b64encode(banner).decode("ascii"))
        else:
            await websocket.send_bytes(banner)
        print("[anthares-browser] VNC RFB greeting forwarded", flush=True)

        async def to_vnc():
            while True:
                message = await websocket.receive()
                if message["type"] == "websocket.disconnect":
                    return
                payload = message.get("bytes")
                if payload is None and message.get("text") is not None:
                    text = message["text"]
                    payload = base64.b64decode(text) if selected == "base64" else text.encode("latin1")
                if payload:
                    writer.write(payload)
                    await writer.drain()

        async def to_browser():
            while True:
                data = await reader.read(65536)
                if not data:
                    return
                if selected == "base64":
                    await websocket.send_text(base64.b64encode(data).decode("ascii"))
                else:
                    await websocket.send_bytes(data)

        async def expire():
            await asyncio.sleep(max(0, expiry - time.time()))
            await websocket.close(code=1008)

        tasks = [asyncio.create_task(fn()) for fn in (to_vnc, to_browser, expire)]
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        for task in done:
            exc = task.exception()
            if exc and not isinstance(exc, WebSocketDisconnect):
                raise exc
    except WebSocketDisconnect:
        return
    except Exception:
        try:
            await websocket.close(code=1011)
        except RuntimeError:
            pass
    finally:
        if writer is not None:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
