#!/usr/bin/env python3
"""Read-only Kwai mobile-web client probe in the already-authenticated Chrome.

A temporary tab shares the current browser context, but CDP overrides apply
only to that tab. No cookies, tokens, storage, URLs, DOM text or media leave it.
This is mobile WEB emulation, not native Kwai Android application identity.
"""
from urllib.parse import urlsplit

ANDROID_UA = (
    "Mozilla/5.0 (Linux; Android 14; Pixel 7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/154.0.0.0 Mobile Safari/537.36"
)
ALLOWED = ("https://www.kwai.com/", "https://studio.kwai.com/")


async def probe_mobile_client(context):
    result = {
        "read_only_probe": True,
        "session_exported": False,
        "native_app_identity": False,
        "mobile_client_emulated": False,
        "mobile_user_agent_active": False,
        "mobile_touch_active": False,
        "mobile_viewport_active": False,
        "kwai_mobile_home_loaded": False,
        "studio_mobile_loaded": False,
        "mobile_home_login_gate": False,
        "mobile_home_create_control": False,
        "mobile_home_file_input": False,
        "studio_mobile_login_gate": False,
        "studio_mobile_file_input": False,
        "studio_mobile_upload_control": False,
        "mobile_upload_ready": False,
    }
    tab = await context.new_page()
    session = None
    try:
        session = await context.new_cdp_session(tab)
        await session.send("Emulation.setDeviceMetricsOverride", {
            "width": 393, "height": 852, "deviceScaleFactor": 2.75,
            "mobile": True, "screenWidth": 393, "screenHeight": 852,
        })
        await session.send("Emulation.setTouchEmulationEnabled", {
            "enabled": True, "maxTouchPoints": 5,
        })
        await session.send("Network.setUserAgentOverride", {
            "userAgent": ANDROID_UA,
            "acceptLanguage": "pt-BR,pt;q=0.9,en-US;q=0.8",
            "platform": "Android",
            "userAgentMetadata": {
                "brands": [
                    {"brand": "Chromium", "version": "154"},
                    {"brand": "Google Chrome", "version": "154"},
                ],
                "fullVersion": "154.0.0.0",
                "platform": "Android", "platformVersion": "14.0.0",
                "architecture": "", "model": "Pixel 7",
                "mobile": True, "bitness": "",
            },
        })
        result["mobile_client_emulated"] = True
        for index, target in enumerate(ALLOWED):
            try:
                await tab.goto(target, wait_until="domcontentloaded", timeout=15000)
                await tab.wait_for_timeout(1500)
                host = urlsplit(tab.url).hostname
                if host not in ("www.kwai.com", "studio.kwai.com"):
                    continue
                flags = await tab.evaluate(r"""() => {
                  const visible = el => {
                    const s=getComputedStyle(el), r=el.getBoundingClientRect();
                    return s.display!=='none' && s.visibility!=='hidden' &&
                      r.width>0 && r.height>0;
                  };
                  const nodes=[...document.querySelectorAll(
                    'a,button,label,[role="button"],[role="menuitem"]'
                  )].filter(visible);
                  const label=el=>((el.innerText||'')+' '+(el.getAttribute('aria-label')||'')).trim();
                  const texts=nodes.map(label).filter(t=>t.length<=90);
                  const login=texts.some(t=>/^(log in|login|sign in|entrar|fazer login)$/i.test(t)) ||
                    [...document.querySelectorAll('input')].some(el=>{
                      const t=(el.type||'').toLowerCase(), n=(el.name||'').toLowerCase();
                      return visible(el)&&(t==='tel'||/phone|email|login/.test(n));
                    });
                  const file=[...document.querySelectorAll('input[type="file"]')]
                    .some(el=>!el.disabled);
                  const create=texts.some(t=>/^(create|criar|new post|novo post|\+)$/i.test(t));
                  const upload=texts.some(t=>/upload|enviar|carregar|album|álbum/i.test(t));
                  return {
                    mobile_ua:/Android/.test(navigator.userAgent)&&/Mobile/.test(navigator.userAgent),
                    touch:navigator.maxTouchPoints>0,
                    viewport:innerWidth<=450 && matchMedia('(pointer: coarse)').matches,
                    login_gate:login, file_input:file, create_control:create,
                    upload_control:upload
                  };
                }""")
                result["mobile_user_agent_active"] |= bool(flags.get("mobile_ua"))
                result["mobile_touch_active"] |= bool(flags.get("touch"))
                result["mobile_viewport_active"] |= bool(flags.get("viewport"))
                if index == 0:
                    result["kwai_mobile_home_loaded"] = True
                    result["mobile_home_login_gate"] = bool(flags.get("login_gate"))
                    result["mobile_home_create_control"] = bool(flags.get("create_control"))
                    result["mobile_home_file_input"] = bool(flags.get("file_input"))
                else:
                    result["studio_mobile_loaded"] = True
                    result["studio_mobile_login_gate"] = bool(flags.get("login_gate"))
                    result["studio_mobile_file_input"] = bool(flags.get("file_input"))
                    result["studio_mobile_upload_control"] = bool(flags.get("upload_control"))
            except Exception:
                continue
        result["mobile_upload_ready"] = (
            result["mobile_client_emulated"]
            and result["mobile_user_agent_active"]
            and result["mobile_touch_active"]
            and result["mobile_viewport_active"]
            and (
                (result["kwai_mobile_home_loaded"] and result["mobile_home_file_input"]
                 and not result["mobile_home_login_gate"])
                or
                (result["studio_mobile_loaded"] and result["studio_mobile_file_input"]
                 and not result["studio_mobile_login_gate"])
            )
        )
        return result
    except Exception:
        result["mobile_cdp_failed"] = True
        return result
    finally:
        try:
            if session is not None:
                await session.detach()
        finally:
            await tab.close()
