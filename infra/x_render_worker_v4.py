import html
import re

from flask import Response, request
from playwright.sync_api import sync_playwright

from x_render_worker_v3 import *

_attempts = 0

PAGE = """<!doctype html><html lang=pt-BR><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>Anthares — ativar X</title><style>body{font-family:system-ui;max-width:760px;margin:40px auto;padding:0 20px;background:#111;color:#eee}textarea{width:100%;height:220px;background:#191919;color:#eee;border:1px solid #555;border-radius:8px;padding:12px}button{padding:12px 20px;font-weight:700;margin-top:12px}code{background:#222;padding:2px 5px}</style><h1>Ativar sessão X no Anthares</h1><p>Uso único. O conteúdo colado não é devolvido na resposta e a página é bloqueada depois da validação.</p><ol><li>No X já logado, abra DevTools → Network e recarregue.</li><li>Em uma requisição para <code>x.com</code>, use Copy → Copy as cURL.</li><li>Cole abaixo e clique em Ativar.</li></ol><form method=post autocomplete=off><textarea name=payload required spellcheck=false></textarea><br><button>Ativar e testar @lucasyahn</button></form></html>"""


def _extract_cookie_header(text):
    for pat in [r"(?:^|\n)cookie:\s*([^\r\n]+)", r"-H\s+[\"']cookie:\s*([^\"']+)[\"']", r"--header\s+[\"']cookie:\s*([^\"']+)[\"']"]:
        m = re.search(pat, text, re.I)
        if m:
            return m.group(1).strip()
    if "=" in text and ";" in text and "\n" not in text.strip():
        return text.strip()
    return ""


def _state_from_cookie_header(value):
    cookies = []
    for part in value.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, val = part.split("=", 1)
        name = name.strip()
        if name:
            cookies.append({"name": name, "value": val.strip(), "domain": ".x.com", "path": "/", "secure": True})
    if not cookies:
        raise RuntimeError("no cookies")
    return {"cookies": cookies, "origins": []}


@app.route("/seed", methods=["GET", "POST"])
def seed():
    global _attempts
    try:
        if _vault_pull():
            return Response("Sessão durável já ativada. Esta página foi bloqueada.", status=410, content_type="text/plain; charset=utf-8")
    except Exception:
        pass
    if request.method == "GET":
        return Response(PAGE, headers={"Cache-Control": "no-store"}, content_type="text/html; charset=utf-8")
    _attempts += 1
    if _attempts > 20:
        return Response("Limite temporário de tentativas atingido.", status=429, content_type="text/plain; charset=utf-8")
    text = request.form.get("payload", "")
    if len(text) > 200000:
        return Response("Conteúdo grande demais.", status=413, content_type="text/plain; charset=utf-8")
    try:
        header = _extract_cookie_header(text)
        if not header:
            raise RuntimeError("cookie header missing")
        state = _state_from_cookie_header(header)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(storage_state=state, viewport={"width": 1280, "height": 900})
            page = context.new_page()
            handle = _identity(page)
            durable = context.storage_state()
            context.close(); browser.close()
        _save_state(durable)
        return Response("OK — @%s validado e sessão salva de forma durável. Pode fechar esta página." % html.escape(handle), headers={"Cache-Control": "no-store"}, content_type="text/plain; charset=utf-8")
    except Exception as exc:
        msg = str(exc).lower()
        safe = "autenticação não validada" if "authentication" in msg or "identity" in msg else "entrada inválida"
        return Response("Falhou: " + safe + ". Nenhum estado foi persistido.", status=400, headers={"Cache-Control": "no-store"}, content_type="text/plain; charset=utf-8")
