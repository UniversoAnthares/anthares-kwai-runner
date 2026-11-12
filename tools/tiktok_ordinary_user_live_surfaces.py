#!/usr/bin/env python3
"""Inspect TikTok ordinary-user LIVE entrypoints in isolated authenticated cloud Chrome.
Read-only browser navigation; never start/end LIVE, publish, request key or expose cookies.
"""
import json, sys
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cortes_tiktok_lucasrosalem4_cloud_publish import state_from_secret
PAGES = [
 ("home","https://www.tiktok.com/"),
 ("account","https://www.tiktok.com/@lucasrosalem4"),
 ("create","https://www.tiktok.com/upload"),
 ("studio","https://www.tiktok.com/tiktokstudio"),
 ("live_studio","https://www.tiktok.com/tiktokstudio/live"),
 ("producer","https://livecenter.tiktok.com/producer")
]
SCRIPT = r"""() => {
 const vis=e => {const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>1 && r.height>1 && s.visibility!=='hidden' && s.display!=='none};
 const elem=[...document.querySelectorAll('button,a,[role="button"],[role="tab"],input')].filter(vis);
 const safe=e=>{let t=(e.innerText||e.getAttribute('aria-label')||e.getAttribute('title')||'').replace(/\s+/g,' ').trim();return t.slice(0,70)};
 const liveRelated=elem.filter(e=>/(live|ao vivo|transmitir|broadcast|criar|create|upload|studio|camera|câmera|go live|entrar ao vivo|iniciar)/i.test(safe(e)));
 const out=liveRelated.slice(0,18).map(e=>({kind:e.tagName.toLowerCase(),role:e.getAttribute('role')||'',text:safe(e),
   disabled:!!e.disabled,href:e.tagName==='A'?(e.getAttribute('href')||'').slice(0,65):null}));
 const body=document.body?.innerText||'';
 return {visible_elements:elem.length,match_count:liveRelated.length,matches:out,
  mentions_live_studio:/live studio/i.test(body),mentions_go_live:/go live|fazer live|iniciar live/i.test(body),
  mentions_get_access:/get access|obter acesso/i.test(body),
  mentions_connect_pc:/connect to pc|conectar ao pc/i.test(body),
  mentions_install_app:/abrir aplicativo|open app|baixar aplicativo|download app/i.test(body),
  has_create_icon:elem.some(e=>/[+＋]/.test(safe(e)) && safe(e).length<15)};
}"""
def main():
 try: state=state_from_secret()
 except Exception as e:print("ACCOUNT_STATE="+type(e).__name__,flush=True);return 3
 with sync_playwright() as p:
  browser=p.chromium.launch(channel="chrome",headless=True,args=["--no-sandbox","--disable-dev-shm-usage","--mute-audio"])
  try:
   results=[]
   for device in ["desktop","mobile"]:
    kwargs={"storage_state":state,"locale":"pt-BR"}
    if device=="mobile":
     model=p.devices["Pixel 7"]
     kwargs.update({k:v for k,v in model.items() if k not in ("default_browser_type",)})
    else:kwargs["viewport"]={"width":1440,"height":900}
    context=browser.new_context(**kwargs)
    page=context.new_page()
    for label,url in PAGES:
     try:
      reply=page.goto(url,wait_until="domcontentloaded",timeout=22000)
      page.wait_for_timeout(1800)
      result=page.evaluate(SCRIPT)
      host=urlsplit(page.url)
      results.append(dict(device=device,page=label,route=host.path[:90],domain_tiktok=bool(host.hostname and host.hostname.endswith("tiktok.com")),
                          http=reply.status if reply else 0,login_required="/login" in host.path.lower(),**result))
     except Exception as e:results.append({"device":device,"page":label,"error":type(e).__name__,"detail":str(e).split("\n")[0][:100]})
    context.close()
   print("NORMAL_USER_TIKTOK_LIVE_SURFACES="+json.dumps(results,ensure_ascii=False,separators=(',',':')),flush=True)
  finally:browser.close()
if __name__=="__main__":sys.exit(main())
