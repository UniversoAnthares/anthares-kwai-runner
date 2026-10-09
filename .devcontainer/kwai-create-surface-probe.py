#!/usr/bin/env python3
"""Sanitized create/upload-surface probe for an existing Kwai browser context.

The module does not export cookies, tokens, storage, page text or screenshots.
It may open disposable Kwai/Studio tabs in the same already-authenticated browser
context, inspect only boolean UI signals, and close those tabs. It never uploads
or publishes.
"""
from urllib.parse import urlsplit

KWAI_HOSTS = {"kwai.com", "www.kwai.com", "studio.kwai.com"}
STUDIO_URL = "https://studio.kwai.com/"
HOME_URL = "https://www.kwai.com/"


def classify_page_signals(signals):
    rows = list(signals or [])
    tab_present = bool(rows)
    login_gate_visible = any(bool(r.get("login_gate_visible")) for r in rows)
    file_input_present = any(bool(r.get("file_input_present")) for r in rows)
    create_control_visible = any(bool(r.get("create_control_visible")) for r in rows)
    upload_control_visible = any(bool(r.get("upload_control_visible")) for r in rows)
    publish_control_visible = any(bool(r.get("publish_control_visible")) for r in rows)
    studio_tab_present = any(bool(r.get("studio_tab_present")) for r in rows)
    mobile_probe_present = any(bool(r.get("mobile_probe")) for r in rows)
    create_or_upload_visible = bool(file_input_present or create_control_visible or upload_control_visible)
    operational_create_surface = any(
        (r.get("file_input_present") or r.get("create_control_visible") or r.get("upload_control_visible"))
        and not r.get("login_gate_visible")
        for r in rows
    )
    return {
        "kwai_tab_present": tab_present,
        "studio_tab_present": studio_tab_present,
        "mobile_probe_present": mobile_probe_present,
        "login_gate_visible": login_gate_visible,
        "file_input_present": file_input_present,
        "create_or_upload_visible": create_or_upload_visible,
        "publish_control_visible": publish_control_visible,
        "operational_create_surface": bool(operational_create_surface),
        "read_only_probe": True,
        "session_exported": False,
    }


async def inspect_page(page, *, mobile_probe=False):
    host = (urlsplit(page.url).hostname or "").lower()
    if host not in KWAI_HOSTS:
        return None
    try:
        flags = await page.evaluate(
            """() => {
              const visible = (el) => {
                if (!el) return false;
                const s = getComputedStyle(el);
                const r = el.getBoundingClientRect();
                return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0;
              };
              const nodes = [...document.querySelectorAll('button,a,[role=button],[role=menuitem],label')];
              const label = (el) => ((el.innerText || el.textContent || '') + ' ' + (el.getAttribute('aria-label') || '') + ' ' + (el.getAttribute('title') || '')).trim();
              const matches = (re) => nodes.some(el => visible(el) && re.test(label(el)));
              const loginInput = [...document.querySelectorAll('input')].some(el => {
                const type = (el.getAttribute('type') || '').toLowerCase();
                const name = (el.getAttribute('name') || '').toLowerCase();
                return visible(el) && (type === 'tel' || /phone|email|login/.test(name));
              });
              const plusLike = nodes.some(el => visible(el) && /^\s*\+\s*$/.test(label(el)));
              const cameraLike = matches(/camera|record|gravar|create video|criar v[ií]deo|new post|novo post/i);
              return {
                login_gate_visible: loginInput || matches(/^(log in|login|sign in|entrar|fazer login)$/i),
                file_input_present: [...document.querySelectorAll('input[type=file]')].some(visible),
                create_control_visible: plusLike || cameraLike || matches(/^(create|criar|new post|novo post)$/i),
                upload_control_visible: matches(/upload|enviar|carregar|album|álbum/i),
                publish_control_visible: matches(/^(publish|post|publicar|share|compartilhar)$/i)
              };
            }"""
        )
    except Exception:
        return None
    return {
        "login_gate_visible": bool(flags.get("login_gate_visible")),
        "file_input_present": bool(flags.get("file_input_present")),
        "create_control_visible": bool(flags.get("create_control_visible")),
        "upload_control_visible": bool(flags.get("upload_control_visible")),
        "publish_control_visible": bool(flags.get("publish_control_visible")),
        "studio_tab_present": host == "studio.kwai.com",
        "mobile_probe": bool(mobile_probe),
    }


async def inspect_existing_pages(context):
    rows = []
    for page in list(getattr(context, "pages", []) or []):
        row = await inspect_page(page)
        if row:
            rows.append(row)
    result = classify_page_signals(rows)
    if result["operational_create_surface"]:
        result["studio_disposable_probe_attempted"] = False
        result["mobile_disposable_probe_attempted"] = False
        return result

    studio = None
    try:
        studio = await context.new_page()
        result["studio_disposable_probe_attempted"] = True
        await studio.goto(STUDIO_URL, wait_until="domcontentloaded", timeout=20000)
        await studio.wait_for_timeout(2500)
        row = await inspect_page(studio)
        if row:
            rows.append(row)
        result = classify_page_signals(rows)
        result["studio_disposable_probe_attempted"] = True
        result["studio_disposable_probe_loaded"] = bool(row)
    except Exception:
        result["studio_disposable_probe_attempted"] = True
        result["studio_disposable_probe_loaded"] = False
    finally:
        if studio is not None:
            try:
                await studio.close()
            except Exception:
                pass

    if result["operational_create_surface"]:
        result["mobile_disposable_probe_attempted"] = False
        return result

    mobile = None
    try:
        mobile = await context.new_page()
        result["mobile_disposable_probe_attempted"] = True
        await mobile.set_viewport_size({"width": 390, "height": 844})
        await mobile.goto(HOME_URL, wait_until="domcontentloaded", timeout=20000)
        await mobile.wait_for_timeout(2500)
        row = await inspect_page(mobile, mobile_probe=True)
        if row:
            rows.append(row)
        result = classify_page_signals(rows)
        result["studio_disposable_probe_attempted"] = True
        result["studio_disposable_probe_loaded"] = True
        result["mobile_disposable_probe_attempted"] = True
        result["mobile_disposable_probe_loaded"] = bool(row)
        return result
    except Exception:
        result["mobile_disposable_probe_attempted"] = True
        result["mobile_disposable_probe_loaded"] = False
        return result
    finally:
        if mobile is not None:
            try:
                await mobile.close()
            except Exception:
                pass
