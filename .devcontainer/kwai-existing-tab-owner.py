#!/usr/bin/env python3
"""Fail-closed exact-owner verification for the live Kwai Chrome session.

No cookies, storage, tokens, screenshots, raw page text, or credentials leave
Chrome. Only boolean evidence is returned. Publication is never attempted.
"""
import importlib.util
from pathlib import Path
from urllib.parse import urlsplit

EXPECTED = "universo.anthares"
KWAI_HOSTS = {"kwai.com", "www.kwai.com"}


def load_guard():
    path = Path(__file__).with_name("kwai-identity-guard.py")
    spec = importlib.util.spec_from_file_location("kwai_identity_guard_owner_probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def open_authenticated_menu(context, guard):
    """Open the signed-in account menu in a disposable tab."""
    page = await context.new_page()
    try:
        await page.goto("https://www.kwai.com/", wait_until="domcontentloaded", timeout=12000)
        await page.wait_for_timeout(700)
        opened = await guard.open_account_menu_in_probe_page(page)
        await page.wait_for_timeout(450)
        evidence = await guard.inspect_open_account_menu(context)
        authenticated = bool(evidence.get("account_menu_logout_visible"))
        exact_link = bool(evidence.get("account_menu_profile_link_matches"))
        return page, bool(opened), authenticated, exact_link
    except Exception:
        try:
            await page.close()
        except Exception:
            pass
        return None, False, False, False


async def react_menu_owner_match(page):
    """Bind the exact handle to the authenticated menu's local React state."""
    try:
        return bool(await page.evaluate(r"""(expected) => {
          const visible = el => {
            if (!el) return false;
            const r=el.getBoundingClientRect(), s=getComputedStyle(el);
            return r.width>0 && r.height>0 && s.display!=='none' && s.visibility!=='hidden';
          };
          const txt = el => (el.innerText || el.textContent || '').trim();
          const logoutRe=/^(log\s*out|logout|sign\s*out|sair|terminar sess[aã]o|encerrar sess[aã]o)$/i;
          const all=[...document.querySelectorAll('a,button,[role="menuitem"],span,div')].filter(visible);
          const logout=all.find(el=>txt(el).length<=40 && logoutRe.test(txt(el)));
          if(!logout) return false;

          const normalize=v=>String(v==null?'':v).trim().replace(/^@/,'').toLowerCase();
          const handleKeys=new Set(['username','user_name','handle','accountname','account_name','kwaiid','kwai_id','uniqueid','unique_id','profilehandle','profile_handle']);
          const secretKey=/token|cookie|secret|password|authorization|session|credential/i;
          const objectHasExpected=(root,maxDepth=4,maxNodes=1400)=>{
            if(!root || (typeof root!=='object' && typeof root!=='function')) return false;
            const queue=[{v:root,d:0}], seen=new WeakSet(); let visited=0;
            while(queue.length && visited<maxNodes){
              const {v,d}=queue.shift();
              if(!v || (typeof v!=='object' && typeof v!=='function') || seen.has(v)) continue;
              seen.add(v); visited++;
              let entries; try { entries=Object.entries(v); } catch(_) { continue; }
              for(const [k,val] of entries){
                if(secretKey.test(k)) continue;
                const key=k.toLowerCase();
                if(handleKeys.has(key) && normalize(val)===expected) return true;
                if(typeof val==='string' && /profile|href|url|link/i.test(k)){
                  try{
                    const u=new URL(val,location.href);
                    if(['kwai.com','www.kwai.com'].includes(u.hostname) && u.pathname.replace(/\/$/,'').toLowerCase()==='/@'+expected) return true;
                  }catch(_){}
                }
                if(d<maxDepth && val && (typeof val==='object'||typeof val==='function')) queue.push({v:val,d:d+1});
              }
            }
            return false;
          };

          let dom=logout;
          for(let level=0; level<7 && dom; level++,dom=dom.parentElement){
            let keys=[]; try { keys=Object.keys(dom); } catch(_){}
            for(const key of keys){
              if(!/^__react(Fiber|Props)\$/.test(key)) continue;
              let fiberOrProps; try { fiberOrProps=dom[key]; } catch(_) { continue; }
              if(key.startsWith('__reactProps$') && objectHasExpected(fiberOrProps,4,1200)) return true;
              if(key.startsWith('__reactFiber$')){
                let fiber=fiberOrProps;
                for(let hops=0; hops<7 && fiber; hops++,fiber=fiber.return){
                  if(fiber.tag===3) break;
                  if(objectHasExpected(fiber.memoizedProps,4,1200)) return true;
                  if(objectHasExpected(fiber.pendingProps,4,1200)) return true;
                  if(objectHasExpected(fiber.memoizedState,3,800)) return true;
                }
              }
            }
            const r=dom.getBoundingClientRect();
            if(r.width>700 || r.height>800) break;
          }
          return false;
        }""", EXPECTED))
    except Exception:
        return False


async def destination_owner_match(page):
    """Verify exact handle on a first-party account/profile/settings destination."""
    try:
        return bool(await page.evaluate(r"""(expected) => {
          const visible=el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden';};
          const norm=v=>String(v==null?'':v).trim().replace(/^@/,'').toLowerCase();
          const text=el=>(el.innerText||el.textContent||'').trim();
          const path=location.pathname.replace(/\/$/,'').toLowerCase();
          const accountish=/profile|account|setting|config|user|me|center/i.test(path);
          const loginRe=/^(log\s*in|sign\s*in|login|entrar|fazer login)$/i;
          const nodes=[...document.querySelectorAll('a[href],button,[role="button"],[role="link"],input,span,div')];
          const loginGate=nodes.some(el=>{if(!visible(el)) return false; const t=text(el); const type=(el.getAttribute?.('type')||'').toLowerCase(); return (t.length<=50&&loginRe.test(t)) || ['email','tel','password'].includes(type);});
          if(loginGate) return false;
          const exactRoute=path==='/@'+expected;
          const exactHref=nodes.some(el=>{if(el.tagName!=='A') return false; try{const u=new URL(el.getAttribute('href')||'',location.href); return ['kwai.com','www.kwai.com'].includes(u.hostname) && u.pathname.replace(/\/$/,'').toLowerCase()==='/@'+expected;}catch(_){return false}});
          const exactInput=nodes.some(el=>{if(el.tagName!=='INPUT') return false; const name=(el.getAttribute('name')||'')+' '+(el.getAttribute('aria-label')||'')+' '+(el.getAttribute('placeholder')||''); return /user|handle|account|kwai|perfil|profile/i.test(name) && norm(el.value)===expected;});
          const exactVisible=nodes.some(el=>{if(!visible(el)) return false; const t=text(el).toLowerCase(); return t==='@'+expected || t===expected;});
          const ownerControl=nodes.some(el=>{if(!visible(el)) return false; const t=text(el), href=el.getAttribute?.('href')||'', testid=el.getAttribute?.('data-testid')||''; return /^(edit profile|editar perfil|account settings|configura[cç][oõ]es da conta)$/i.test(t) || /edit[-_ ]?profile|profile[-_ ]?edit/i.test(testid) || /\/(profile|account)\/(edit|settings)(\/|$)/i.test(href);});
          return exactRoute || (accountish && (exactHref||exactInput||exactVisible) && ownerControl);
        }""", EXPECTED))
    except Exception:
        return False


async def safe_menu_destinations(context, guard):
    """Try only safe account/profile/settings rows from the authenticated menu."""
    labels=("profile","perfil","my profile","meu perfil","account","conta","settings","configurações","configuracoes","account settings","configurações da conta","configuracoes da conta")
    for wanted in labels:
        before=list(context.pages); page=await context.new_page()
        try:
            await page.goto("https://www.kwai.com/", wait_until="domcontentloaded", timeout=12000)
            await page.wait_for_timeout(700)
            if not await guard.open_account_menu_in_probe_page(page): continue
            await page.wait_for_timeout(450)
            point=await page.evaluate(r"""(wanted) => {
              const visible=el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden';};
              const txt=el=>[(el.innerText||el.textContent||''),(el.getAttribute('aria-label')||''),(el.getAttribute('title')||'')].join(' ').replace(/\s+/g,' ').trim().toLowerCase();
              const logoutRe=/^(log\s*out|logout|sign\s*out|sair|terminar sess[aã]o|encerrar sess[aã]o)$/i;
              const blocked=/(log\s*out|logout|sign\s*out|sair|delete|remove|excluir|apagar|publish|publicar|postar|upload|enviar)/i;
              const nodes=[...document.querySelectorAll('a[href],button,[role="button"],[role="menuitem"],[role="link"],span,div')].filter(visible);
              const logout=nodes.find(el=>(el.innerText||'').trim().length<=40 && logoutRe.test((el.innerText||'').trim()));
              if(!logout) return null;
              let panel=logout;
              for(let i=0;i<8&&panel;i++,panel=panel.parentElement){
                const r=panel.getBoundingClientRect();
                if(r.width<110||r.width>560||r.height<60||r.height>760||r.right<innerWidth*.60) continue;
                const candidates=[...panel.querySelectorAll('a[href],button,[role="button"],[role="menuitem"],[role="link"],span,div')].filter(el=>{
                  if(!visible(el)) return false;
                  const t=txt(el), r2=el.getBoundingClientRect();
                  if(blocked.test(t)||t.length>100||r2.width<20||r2.height<16||r2.height>130) return false;
                  if(t===wanted) return true;
                  if(el.tagName==='A'){
                    const href=(el.getAttribute('href')||'').toLowerCase();
                    if(['profile','perfil','my profile','meu perfil'].includes(wanted)) return /\/(profile|user|me)(\/|$)|\/@[^/]+\/?$/.test(href);
                    if(['account','conta','account settings','configurações da conta','configuracoes da conta'].includes(wanted)) return /\/(account|settings?)(\/|$)/.test(href);
                    if(wanted==='settings'||wanted.startsWith('config')) return /\/settings?(\/|$)/.test(href);
                  }
                  return false;
                }).sort((a,b)=>a.getBoundingClientRect().top-b.getBoundingClientRect().top);
                if(candidates.length){const r3=candidates[0].getBoundingClientRect(); return {x:r3.left+r3.width/2,y:r3.top+r3.height/2};}
              }
              return null;
            }""", wanted)
            if not point: continue
            await page.mouse.click(point["x"],point["y"])
            for _ in range(16):
                await page.wait_for_timeout(350)
                opened=[p for p in context.pages if p not in before and p!=page]
                for candidate in [page]+opened:
                    if urlsplit(candidate.url).hostname not in KWAI_HOSTS: continue
                    if await destination_owner_match(candidate): return True
        except Exception:
            pass
        finally:
            for extra in list(context.pages):
                if extra not in before:
                    try: await extra.close()
                    except Exception: pass
    return False


async def inspect_existing_tab(context):
    guard=load_guard()
    page, opened, authenticated, exact_link=await open_authenticated_menu(context,guard)
    if not page:
        return {"chrome_connected":True,"authenticated_ui_detected":False,"exact_owner_menu_link":False,"react_owner_match":False,"settings_owner_match":False,"exact_owner_navigation":False,"identity_verified":False,"session_exported":False}
    try:
        react_match=await react_menu_owner_match(page) if authenticated else False
    finally:
        try: await page.close()
        except Exception: pass
    if authenticated and (exact_link or react_match):
        return {"chrome_connected":True,"authenticated_ui_detected":True,"exact_owner_menu_link":exact_link,"react_owner_match":react_match,"settings_owner_match":False,"exact_owner_navigation":False,"identity_verified":True,"session_exported":False}
    settings_match=await safe_menu_destinations(context,guard) if authenticated else False
    if settings_match:
        return {"chrome_connected":True,"authenticated_ui_detected":True,"exact_owner_menu_link":exact_link,"react_owner_match":react_match,"settings_owner_match":True,"exact_owner_navigation":True,"identity_verified":True,"session_exported":False}
    navigation=await guard.inspect_own_profile_navigation(context)
    nav_match=bool(navigation.get("account_menu_profile_navigation_matches"))
    if authenticated and nav_match:
        return {"chrome_connected":True,"authenticated_ui_detected":True,"exact_owner_menu_link":exact_link,"react_owner_match":react_match,"settings_owner_match":settings_match,"exact_owner_navigation":True,"identity_verified":True,"session_exported":False}
    independent=await guard.inspect_profile_without_logout(context)
    independent_owner=bool(independent.get("profile_navigation_matches") is True and independent.get("profile_owner_control_visible") is True and independent.get("profile_login_controls_absent") is True)
    return {"chrome_connected":True,"authenticated_ui_detected":bool(authenticated or independent_owner),"exact_owner_menu_link":exact_link,"react_owner_match":react_match,"settings_owner_match":settings_match,"exact_owner_navigation":bool(nav_match or independent_owner),"identity_verified":independent_owner,"session_exported":False}
