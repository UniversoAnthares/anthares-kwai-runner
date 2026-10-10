#!/usr/bin/env python3
"""Fail-closed exact-owner verification from authenticated Kwai creator UI.

No cookies, storage, tokens, screenshots, raw page text, or credentials leave
Chrome. Only boolean evidence is returned. No media is selected and Publish/Post
is never clicked.
"""
import importlib.util
from pathlib import Path
from urllib.parse import urlsplit

EXPECTED = "lucasrosalem"
KWAI_HOSTS = {"kwai.com", "www.kwai.com", "studio.kwai.com"}


def load_module(filename, name):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def prove_authenticated(context, guard):
    page = await context.new_page()
    try:
        await page.goto("https://www.kwai.com/", wait_until="domcontentloaded", timeout=12000)
        await page.wait_for_timeout(700)
        await guard.open_account_menu_in_probe_page(page)
        await page.wait_for_timeout(450)
        evidence = await guard.inspect_open_account_menu(context)
        return bool(evidence.get("account_menu_logout_visible")), bool(evidence.get("account_menu_profile_link_matches"))
    except Exception:
        return False, False
    finally:
        try:
            await page.close()
        except Exception:
            pass


async def creator_surface_identity(page):
    """Require creator/create context plus exact self-account evidence."""
    try:
        host = (urlsplit(page.url).hostname or "").lower()
        if host not in KWAI_HOSTS:
            return False
        return bool(await page.evaluate(r"""(expected) => {
          const visible = el => {
            if (!el) return false;
            const r=el.getBoundingClientRect(), s=getComputedStyle(el);
            return r.width>0 && r.height>0 && s.display!=='none' && s.visibility!=='hidden';
          };
          const text = el => (el.innerText || el.textContent || '').trim();
          const path = location.pathname.toLowerCase();
          const host = location.hostname.toLowerCase();
          const nodes=[...document.querySelectorAll('a[href],button,[role="button"],[role="link"],input,span,div,[data-testid]')];
          const loginRe=/^(log\s*in|sign\s*in|login|entrar|fazer login)$/i;
          const loginGate=nodes.some(el=>{
            if(!visible(el)) return false;
            const t=text(el), type=(el.getAttribute?.('type')||'').toLowerCase();
            return (t.length<=50 && loginRe.test(t)) || ['email','tel','password'].includes(type);
          });
          if(loginGate) return false;

          const surface = host==='studio.kwai.com' ||
            /creator|studio|upload|publish|post|content|center/.test(path) ||
            nodes.some(el=>visible(el) && /creator\s*(center|centre)|central do criador|centro do criador|upload|enviar|carregar|create video|criar v[ií]deo/i.test(text(el)));
          if(!surface) return false;

          const normalize=v=>String(v==null?'':v).trim().replace(/^@/,'').toLowerCase();
          const exactRoute=location.pathname.replace(/\/$/,'').toLowerCase()==='/@'+expected;
          const exactHref=nodes.some(el=>{
            if(el.tagName!=='A') return false;
            try {
              const u=new URL(el.getAttribute('href')||'', location.href);
              return ['kwai.com','www.kwai.com'].includes(u.hostname) &&
                u.pathname.replace(/\/$/,'').toLowerCase()==='/@'+expected;
            } catch (_) { return false; }
          });
          const exactInput=nodes.some(el=>{
            if(el.tagName!=='INPUT') return false;
            const key=((el.getAttribute('name')||'')+' '+(el.getAttribute('aria-label')||'')+' '+(el.getAttribute('placeholder')||'')).toLowerCase();
            return /user|handle|account|kwai|perfil|profile/.test(key) && normalize(el.value)===expected;
          });
          const exactVisible=nodes.some(el=>{
            if(!visible(el)) return false;
            const t=text(el).toLowerCase();
            return t==='@'+expected || t===expected;
          });
          const ownerControl=nodes.some(el=>{
            if(!visible(el)) return false;
            const t=text(el), href=el.getAttribute?.('href')||'', testid=el.getAttribute?.('data-testid')||'';
            return /^(edit profile|editar perfil|account settings|configura[cç][oõ]es da conta|creator center|creator centre|central do criador|centro do criador)$/i.test(t) ||
              /edit[-_ ]?profile|profile[-_ ]?edit|creator[-_ ]?(center|centre)/i.test(testid) ||
              /\/(profile|account)\/(edit|settings)(\/|$)/i.test(href);
          });

          const selfKeys=new Set(['isself','isme','isowner','ismine','iscurrentuser','self','owner']);
          const handleKeys=new Set(['username','user_name','handle','accountname','account_name','kwaiid','kwai_id','uniqueid','unique_id','profilehandle','profile_handle']);
          const secretKey=/token|cookie|secret|password|authorization|session|credential/i;
          const strongState=root=>{
            if(!root || (typeof root!=='object' && typeof root!=='function')) return false;
            const q=[{v:root,d:0}], seen=new WeakSet(); let visited=0;
            while(q.length && visited<1800){
              const {v,d}=q.shift();
              if(!v || (typeof v!=='object'&&typeof v!=='function') || seen.has(v)) continue;
              seen.add(v); visited++;
              let entries; try { entries=Object.entries(v); } catch (_) { continue; }
              let selfFlag=false, exactHandle=false;
              for(const [k,val] of entries){
                if(secretKey.test(k)) continue;
                const key=k.toLowerCase();
                if(selfKeys.has(key) && val===true) selfFlag=true;
                if(handleKeys.has(key) && normalize(val)===expected) exactHandle=true;
              }
              if(selfFlag && exactHandle) return true;
              if(d<4){
                for(const [k,val] of entries){
                  if(secretKey.test(k)) continue;
                  if(val && (typeof val==='object'||typeof val==='function')) q.push({v:val,d:d+1});
                }
              }
            }
            return false;
          };
          let selfState=false;
          const reactNodes=nodes.filter(el=>visible(el)).slice(0,350);
          for(const el of reactNodes){
            let keys=[]; try { keys=Object.keys(el); } catch (_) {}
            for(const key of keys){
              if(!/^__react(Fiber|Props)\$/.test(key)) continue;
              let value; try { value=el[key]; } catch (_) { continue; }
              if(key.startsWith('__reactProps$') && strongState(value)){selfState=true;break;}
              if(key.startsWith('__reactFiber$')){
                let fiber=value;
                for(let hops=0;hops<6&&fiber;hops++,fiber=fiber.return){
                  if(fiber.tag===3) break;
                  if(strongState(fiber.memoizedProps)||strongState(fiber.pendingProps)||strongState(fiber.memoizedState)){selfState=true;break;}
                }
              }
              if(selfState) break;
            }
            if(selfState) break;
          }
          return exactRoute || selfState || ((exactHref||exactInput||exactVisible) && ownerControl);
        }""", EXPECTED))
    except Exception:
        return False


async def creator_center_probe(context, guard):
    before=list(context.pages)
    page=await context.new_page()
    try:
        await page.goto("https://www.kwai.com/", wait_until="domcontentloaded", timeout=12000)
        await page.wait_for_timeout(700)
        if not await guard.open_account_menu_in_probe_page(page):
            return False
        await page.wait_for_timeout(450)
        point=await page.evaluate(r"""() => {
          const visible=el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'};
          const label=el=>[(el.innerText||el.textContent||''),(el.getAttribute('aria-label')||''),(el.getAttribute('title')||'')].join(' ').replace(/\s+/g,' ').trim();
          const nodes=[...document.querySelectorAll('a[href],button,[role="button"],[role="menuitem"],[role="link"],span,div')].filter(visible);
          const re=/^(creator\s*(center|centre)|central do criador|centro do criador|centro de criadores|centro del creador)$/i;
          const item=nodes.find(el=>label(el).length<=80&&re.test(label(el)));
          if(!item) return null;
          let target=item;
          for(let i=0;i<4&&target.parentElement;i++){
            const tag=target.tagName||'',role=target.getAttribute?.('role')||'';
            if(tag==='A'||tag==='BUTTON'||['button','menuitem','link'].includes(role)||target.tabIndex>=0) break;
            target=target.parentElement;
          }
          const r=target.getBoundingClientRect();
          return {x:r.left+r.width/2,y:r.top+r.height/2};
        }""")
        if not point:
            return False
        await page.mouse.click(point["x"],point["y"])
        for _ in range(18):
            await page.wait_for_timeout(350)
            opened=[p for p in context.pages if p not in before and p!=page]
            for candidate in [page]+opened:
                if await creator_surface_identity(candidate):
                    return True
        return False
    except Exception:
        return False
    finally:
        for extra in list(context.pages):
            if extra not in before:
                try: await extra.close()
                except Exception: pass


async def create_surface_probe(context, create_probe):
    before=list(context.pages)
    page=await context.new_page()
    try:
        await page.goto("https://www.kwai.com/", wait_until="domcontentloaded", timeout=12000)
        await page.wait_for_timeout(700)
        flags=await create_probe.page_flags(page)
        if not flags or flags.get("login_gate_visible"):
            return False
        point=await create_probe.activation_point(page)
        if not point:
            return False
        await page.mouse.click(point["x"],point["y"])
        for _ in range(18):
            await page.wait_for_timeout(350)
            opened=[p for p in context.pages if p not in before and p!=page]
            for candidate in [page]+opened:
                if await creator_surface_identity(candidate):
                    return True
        return False
    except Exception:
        return False
    finally:
        for extra in list(context.pages):
            if extra not in before:
                try: await extra.close()
                except Exception: pass


async def studio_probe(context):
    page=await context.new_page()
    try:
        await page.goto("https://studio.kwai.com/", wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(1400)
        return await creator_surface_identity(page)
    except Exception:
        return False
    finally:
        try: await page.close()
        except Exception: pass


async def inspect_existing_tab(context):
    guard=load_module("kwai-identity-guard.py","kwai_identity_guard_owner_creator")
    create_probe=load_module("kwai-create-surface-probe.py","kwai_create_surface_owner_creator")
    authenticated, exact_link=await prove_authenticated(context,guard)
    if not authenticated:
        return {"chrome_connected":True,"authenticated_ui_detected":False,"exact_owner_menu_link":False,"creator_center_owner_match":False,"create_surface_owner_match":False,"studio_owner_match":False,"identity_verified":False,"session_exported":False}
    if exact_link:
        return {"chrome_connected":True,"authenticated_ui_detected":True,"exact_owner_menu_link":True,"creator_center_owner_match":False,"create_surface_owner_match":False,"studio_owner_match":False,"identity_verified":True,"session_exported":False}

    creator_match=await creator_center_probe(context,guard)
    if creator_match:
        return {"chrome_connected":True,"authenticated_ui_detected":True,"exact_owner_menu_link":False,"creator_center_owner_match":True,"create_surface_owner_match":False,"studio_owner_match":False,"identity_verified":True,"session_exported":False}

    create_match=await create_surface_probe(context,create_probe)
    if create_match:
        return {"chrome_connected":True,"authenticated_ui_detected":True,"exact_owner_menu_link":False,"creator_center_owner_match":False,"create_surface_owner_match":True,"studio_owner_match":False,"identity_verified":True,"session_exported":False}

    studio_match=await studio_probe(context)
    if studio_match:
        return {"chrome_connected":True,"authenticated_ui_detected":True,"exact_owner_menu_link":False,"creator_center_owner_match":False,"create_surface_owner_match":False,"studio_owner_match":True,"identity_verified":True,"session_exported":False}

    navigation=await guard.inspect_own_profile_navigation(context)
    nav_match=bool(navigation.get("account_menu_profile_navigation_matches"))
    independent=await guard.inspect_profile_without_logout(context)
    independent_owner=bool(independent.get("profile_navigation_matches") is True and independent.get("profile_owner_control_visible") is True and independent.get("profile_login_controls_absent") is True)
    verified=bool(nav_match or independent_owner)
    return {"chrome_connected":True,"authenticated_ui_detected":True,"exact_owner_menu_link":False,"creator_center_owner_match":False,"create_surface_owner_match":False,"studio_owner_match":False,"exact_owner_navigation":verified,"identity_verified":verified,"session_exported":False}
