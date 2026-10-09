#!/usr/bin/env python3
"""Read-only classifier for the existing Kwai/Studio browser context.

This module never launches a browser, never clicks, never uploads, never publishes,
and never exports page text or browser/session material.  Its public result is a
small set of booleans suitable for the public command bridge.
"""
from urllib.parse import urlsplit

KWAI_HOSTS = {"kwai.com", "www.kwai.com", "studio.kwai.com"}


def classify_page_signals(signals):
    """Collapse per-page sanitized signals into one fail-closed result."""
    rows = list(signals or [])
    tab_present = bool(rows)
    login_gate_visible = any(bool(r.get("login_gate_visible")) for r in rows)
    file_input_present = any(bool(r.get("file_input_present")) for r in rows)
    create_control_visible = any(bool(r.get("create_control_visible")) for r in rows)
    upload_control_visible = any(bool(r.get("upload_control_visible")) for r in rows)
    publish_control_visible = any(bool(r.get("publish_control_visible")) for r in rows)
    studio_tab_present = any(bool(r.get("studio_tab_present")) for r in rows)
    create_or_upload_visible = bool(file_input_present or create_control_visible or upload_control_visible)
    operational_create_surface = bool(tab_present and create_or_upload_visible and not login_gate_visible)
    return {
        "kwai_tab_present": tab_present,
        "studio_tab_present": studio_tab_present,
        "login_gate_visible": login_gate_visible,
        "file_input_present": file_input_present,
        "create_or_upload_visible": create_or_upload_visible,
        "publish_control_visible": publish_control_visible,
        "operational_create_surface": operational_create_surface,
        "read_only_probe": True,
        "session_exported": False,
    }


async def inspect_existing_pages(context):
    """Inspect only pages already present in the supplied browser context."""
    rows = []
    for page in list(getattr(context, "pages", []) or []):
        try:
            host = (urlsplit(page.url).hostname or "").lower()
        except Exception:
            continue
        if host not in KWAI_HOSTS:
            continue
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
                  const matches = (re) => nodes.some(el => visible(el) && re.test((el.innerText || el.textContent || '').trim()));
                  const loginInput = [...document.querySelectorAll('input')].some(el => {
                    const type = (el.getAttribute('type') || '').toLowerCase();
                    const name = (el.getAttribute('name') || '').toLowerCase();
                    return visible(el) && (type === 'tel' || /phone|email|login/.test(name));
                  });
                  return {
                    login_gate_visible: loginInput || matches(/^(log in|login|sign in|entrar)$/i),
                    file_input_present: [...document.querySelectorAll('input[type=file]')].some(visible),
                    create_control_visible: matches(/^(create|criar|new post|novo post)$/i),
                    upload_control_visible: matches(/^(upload|enviar|carregar)$/i),
                    publish_control_visible: matches(/^(publish|post|publicar)$/i)
                  };
                }"""
            )
        except Exception:
            continue
        rows.append({
            "login_gate_visible": bool(flags.get("login_gate_visible")),
            "file_input_present": bool(flags.get("file_input_present")),
            "create_control_visible": bool(flags.get("create_control_visible")),
            "upload_control_visible": bool(flags.get("upload_control_visible")),
            "publish_control_visible": bool(flags.get("publish_control_visible")),
            "studio_tab_present": host == "studio.kwai.com",
        })
    return classify_page_signals(rows)
