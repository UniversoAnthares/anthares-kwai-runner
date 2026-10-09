#!/usr/bin/env python3
"""Sanitized create/upload probe for the already-authenticated Kwai browser.

No cookies, tokens, storage, page text or screenshots are exported. The probe may
click only a visible create/upload control, observes boolean UI state, then restores
the original tab. It never selects a file and never clicks Publish/Post.
"""
from urllib.parse import urlsplit

KWAI_HOSTS={"kwai.com","www.kwai.com","studio.kwai.com"}


def classify_page_signals(signals):
    rows=list(signals or [])
    login=any(bool(r.get("login_gate_visible")) for r in rows)
    file_input=any(bool(r.get("file_input_present")) for r in rows)
    create=any(bool(r.get("create_control_visible")) for r in rows)
    upload=any(bool(r.get("upload_control_visible")) for r in rows)
    publish=any(bool(r.get("publish_control_visible")) for r in rows)
    operational=any((r.get("file_input_present") or r.get("create_control_visible") or r.get("upload_control_visible")) and not r.get("login_gate_visible") for r in rows)
    return {"kwai_tab_present":bool(rows),"studio_tab_present":any(bool(r.get("studio_tab_present")) for r in rows),"login_gate_visible":login,"file_input_present":file_input,"create_or_upload_visible":bool(file_input or create or upload),"publish_control_visible":publish,"operational_create_surface":bool(operational),"session_exported":False}


async def page_flags(page):
    try:
        host=(urlsplit(page.url).hostname or "").lower()
    except Exception:return None
    if host not in KWAI_HOSTS:return None
    try:
        f=await page.evaluate(r"""() => {
          const vis=e=>{if(!e)return false;const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'};
          const nodes=[...document.querySelectorAll('button,a,[role=button],[role=menuitem],label')];
          const lab=e=>((e.innerText||e.textContent||'')+' '+(e.getAttribute('aria-label')||'')+' '+(e.getAttribute('title')||'')).trim();
          const match=re=>nodes.some(e=>vis(e)&&re.test(lab(e)));
          const loginInput=[...document.querySelectorAll('input')].some(e=>{const t=(e.type||'').toLowerCase(),n=(e.name||'').toLowerCase();return vis(e)&&(t==='tel'||/phone|email|login/.test(n))});
          return {
            login_gate_visible:loginInput||match(/^(log\s*in|login|sign\s*in|entrar|fazer login)$/i),
            file_input_present:[...document.querySelectorAll('input[type=file]')].some(vis),
            create_control_visible:nodes.some(e=>vis(e)&&(/^\s*\+\s*$/.test(lab(e))||/camera|record|gravar|create video|criar v[ií]deo|new post|novo post|create|criar/i.test(lab(e)))),
            upload_control_visible:match(/upload|enviar|carregar|album|álbum/i),
            publish_control_visible:match(/^(publish|post|publicar|share|compartilhar)$/i)
          };
        }""")
    except Exception:return None
    return {**f,"studio_tab_present":host=="studio.kwai.com"}


async def activation_point(page):
    try:
        return await page.evaluate(r"""() => {
          const vis=e=>{if(!e)return false;const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'};
          const lab=e=>((e.innerText||e.textContent||'')+' '+(e.getAttribute('aria-label')||'')+' '+(e.getAttribute('title')||'')).trim();
          const nodes=[...document.querySelectorAll('button,a,[role=button],label')].filter(vis);
          const ranked=nodes.map(e=>({e,t:lab(e)})).filter(x=>/^\s*\+\s*$/.test(x.t)||/camera|record|gravar|create video|criar v[ií]deo|new post|novo post|upload|enviar|carregar|create|criar/i.test(x.t)).filter(x=>!/(publish|postar|publicar|logout|log out|sign out|sair)/i.test(x.t));
          if(!ranked.length)return null;
          const e=ranked[0].e,r=e.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2};
        }""")
    except Exception:return None


async def activate_existing(context,page):
    out={"activation_probe_attempted":True,"activation_existing_tab":True,"activation_control_clicked":False,"activation_file_input_present":False,"activation_login_gate_visible":False,"activation_surface_ready":False}
    try:
        before=await page_flags(page)
        if not before or before.get("login_gate_visible"):out["activation_login_gate_visible"]=bool(before and before.get("login_gate_visible"));return out
        p=await activation_point(page)
        if not p:return out
        old_url=page.url
        old_pages=set(context.pages)
        await page.mouse.click(p["x"],p["y"])
        out["activation_control_clicked"]=True
        await page.wait_for_timeout(2200)
        new_pages=[x for x in context.pages if x not in old_pages]
        target=new_pages[-1] if new_pages else page
        after=await page_flags(target)
        if after:
            out["activation_file_input_present"]=bool(after.get("file_input_present"))
            out["activation_login_gate_visible"]=bool(after.get("login_gate_visible"))
            out["activation_create_or_upload_visible"]=bool(after.get("create_control_visible") or after.get("upload_control_visible"))
            out["activation_publish_control_visible"]=bool(after.get("publish_control_visible"))
            out["activation_surface_ready"]=bool((after.get("file_input_present") or after.get("create_control_visible") or after.get("upload_control_visible")) and not after.get("login_gate_visible"))
        for x in new_pages:
            try:await x.close()
            except Exception:pass
        if not new_pages:
            try:
                await page.keyboard.press("Escape");await page.wait_for_timeout(250)
                if page.url!=old_url:await page.go_back(wait_until="domcontentloaded",timeout=7000)
            except Exception:pass
        return out
    except Exception:
        out["activation_probe_failed"]=True;return out


async def inspect_existing_pages(context):
    rows=[]; candidates=[]
    for page in list(getattr(context,"pages",[]) or []):
        f=await page_flags(page)
        if f:
            rows.append(f)
            if (f.get("create_control_visible") or f.get("upload_control_visible") or f.get("file_input_present")) and not f.get("login_gate_visible"):
                candidates.append(page)
    result=classify_page_signals(rows)
    if candidates:
        result.update(await activate_existing(context,candidates[0]))
    else:
        result.update({"activation_probe_attempted":True,"activation_existing_tab":False,"activation_control_clicked":False,"activation_file_input_present":False,"activation_login_gate_visible":False,"activation_surface_ready":False})
    return result
