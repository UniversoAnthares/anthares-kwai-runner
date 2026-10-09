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


async def open_menu_page(context, guard):
    page = await context.new_page()
    try:
        await page.goto("https://www.kwai.com/", wait_until="domcontentloaded", timeout=12000)
        await page.wait_for_timeout(700)
        await guard.open_account_menu_in_probe_page(page)
        await page.wait_for_timeout(450)
        evidence = await guard.inspect_open_account_menu(context)
        return page, bool(evidence.get("account_menu_logout_visible")), bool(evidence.get("account_menu_profile_link_matches"))
    except Exception:
        try:
            await page.close()
        except Exception:
            pass
        return None, False, False


async def menu_subtree_owner_match(page):
    """Scan only the authenticated dropdown subtree and nearby React state."""
    try:
        return bool(await page.evaluate(r"""(expected) => {
          const visible=el=>{if(!el)return false;const r=el.getBoundingClientRect(),s=getComputedStyle(el);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'};
          const txt=el=>(el.innerText||el.textContent||'').trim();
          const logoutRe=/^(log\s*out|logout|sign\s*out|sair|terminar sess[aã]o|encerrar sess[aã]o)$/i;
          const nodes=[...document.querySelectorAll('a,button,[role="menuitem"],span,div')].filter(visible);
          const logout=nodes.find(el=>txt(el).length<=40&&logoutRe.test(txt(el)));
          if(!logout)return false;
          let panel=null,node=logout;
          for(let i=0;i<8&&node;i++,node=node.parentElement){const r=node.getBoundingClientRect();if(visible(node)&&r.width>=100&&r.width<=600&&r.height>=60&&r.height<=800&&r.right>=innerWidth*.55){panel=node;break;}}
          if(!panel)return false;
          const normalize=v=>String(v==null?'':v).trim().replace(/^@/,'').toLowerCase();
          const strongKey=/^(username|user_name|handle|accountname|account_name|kwaiid|kwai_id|uniqueid|unique_id|profilehandle|profile_handle)$/i;
          const contextualKey=/(user.*name|handle|kwai.*id|account.*name|profile.*(name|handle|url)|unique.*id|nickname|href|url|link)/i;
          const secretKey=/token|cookie|secret|password|authorization|session|credential/i;
          const objectHasExpected=(root,maxDepth=4,maxNodes=900)=>{
            if(!root||(typeof root!=='object'&&typeof root!=='function'))return false;
            const q=[{v:root,d:0}],seen=new WeakSet();let n=0;
            while(q.length&&n<maxNodes){const {v,d}=q.shift();if(!v||(typeof v!=='object'&&typeof v!=='function')||seen.has(v))continue;seen.add(v);n++;let entries;try{entries=Object.entries(v)}catch(_){continue}for(const [k,val] of entries){if(secretKey.test(k))continue;if(strongKey.test(k)&&normalize(val)===expected)return true;if(typeof val==='string'&&contextualKey.test(k)){if(normalize(val)===expected)return true;try{const u=new URL(val,location.href);if(['kwai.com','www.kwai.com'].includes(u.hostname)&&u.pathname.replace(/\/$/,'').toLowerCase()==='/@'+expected)return true;}catch(_){}}if(d<maxDepth&&val&&(typeof val==='object'||typeof val==='function'))q.push({v:val,d:d+1});}}
            return false;
          };
          for(const el of [panel,...panel.querySelectorAll('*')]){try{const href=el.getAttribute?.('href')||'';if(href){const u=new URL(href,location.href);if(['kwai.com','www.kwai.com'].includes(u.hostname)&&u.pathname.replace(/\/$/,'').toLowerCase()==='/@'+expected)return true;}for(const name of ['data-username','data-user-name','data-handle','data-account','data-profile']){if(normalize(el.getAttribute?.(name))===expected)return true;}}catch(_){}}
          const els=[panel,...panel.querySelectorAll('*')].slice(0,450);
          for(const el of els){let keys=[];try{keys=Object.keys(el)}catch(_){}for(const key of keys){if(!/^__react(Fiber|Props)\$/.test(key))continue;let value;try{value=el[key]}catch(_){continue}if(key.startsWith('__reactProps$')&&objectHasExpected(value,4,900))return true;if(key.startsWith('__reactFiber$')){let fiber=value;for(let hops=0;hops<5&&fiber;hops++,fiber=fiber.return){if(fiber.tag===3)break;if(objectHasExpected(fiber.memoizedProps,4,900))return true;if(objectHasExpected(fiber.pendingProps,4,900))return true;if(objectHasExpected(fiber.memoizedState,3,600))return true;}}}}
          return false;
        }""", EXPECTED))
    except Exception:
        return False


async def page_is_expected_owner_destination(page):
    try:
        return bool(await page.evaluate(r"""(expected) => {
          const visible=el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'};
          const text=el=>(el.innerText||el.textContent||'').trim().toLowerCase();
          const path=location.pathname.replace(/\/$/,'').toLowerCase();
          const nodes=[...document.querySelectorAll('a[href],button,[role="button"],input,span,div')];
          const login=nodes.some(el=>visible(el)&&/^(log\s*in|sign\s*in|login|entrar|fazer login)$/i.test((el.innerText||'').trim()));if(login)return false;
          if(path==='/@'+expected)return true;
          const accountish=/profile|account|setting|config|user|center|me/i.test(path);if(!accountish)return false;
          const exactHandle=nodes.some(el=>{if(el.tagName==='INPUT'){const key=((el.getAttribute('name')||'')+' '+(el.getAttribute('aria-label')||'')+' '+(el.getAttribute('placeholder')||'')).toLowerCase();return /user|handle|account|kwai|perfil|profile/.test(key)&&String(el.value||'').trim().replace(/^@/,'').toLowerCase()===expected;}return visible(el)&&(text(el)==='@'+expected||text(el)===expected);});
          const ownerControl=nodes.some(el=>visible(el)&&/^(edit profile|editar perfil|account settings|configura[cç][oõ]es da conta)$/i.test((el.innerText||'').trim()));
          return exactHandle&&ownerControl;
        }""", EXPECTED))
    except Exception:
        return False


async def menu_geometry_owner_match(context, guard):
    """Click only non-dangerous targets above Log out inside the account menu."""
    for slot in range(12):
        before=list(context.pages);page=await context.new_page()
        try:
            await page.goto("https://www.kwai.com/", wait_until="domcontentloaded", timeout=12000)
            await page.wait_for_timeout(700)
            if not await guard.open_account_menu_in_probe_page(page):continue
            await page.wait_for_timeout(450)
            points=await page.evaluate(r"""() => {
              const visible=el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'};
              const text=el=>(el.innerText||el.textContent||'').trim();
              const logoutRe=/^(log\s*out|logout|sign\s*out|sair|terminar sess[aã]o|encerrar sess[aã]o)$/i;
              const blocked=/(log\s*out|logout|sign\s*out|sair|delete|remove|excluir|apagar|publish|publicar|postar|upload|enviar|deactivate|desativar)/i;
              const all=[...document.querySelectorAll('a,button,[role="button"],[role="menuitem"],[role="link"],span,div,img')].filter(visible);
              const logout=all.find(el=>text(el).length<=40&&logoutRe.test(text(el)));if(!logout)return [];
              let panel=null,node=logout;for(let i=0;i<8&&node;i++,node=node.parentElement){const r=node.getBoundingClientRect();if(visible(node)&&r.width>=100&&r.width<=600&&r.height>=60&&r.height<=800&&r.right>=innerWidth*.55){panel=node;break;}}if(!panel)return [];
              const lr=logout.getBoundingClientRect(),rows=[];
              const add=el=>{if(!el||!visible(el)||!panel.contains(el))return;let target=el;for(let i=0;i<4&&target.parentElement&&panel.contains(target.parentElement);i++){const role=target.getAttribute?.('role')||'',tag=target.tagName||'',clickable=tag==='A'||tag==='BUTTON'||['button','menuitem','link'].includes(role)||target.tabIndex>=0||getComputedStyle(target).cursor==='pointer';if(clickable)break;target=target.parentElement;}const r=target.getBoundingClientRect(),t=text(target);if(r.bottom>lr.top+3||r.top<panel.getBoundingClientRect().top-2)return;if(r.width<24||r.height<18||r.width>560||r.height>150)return;if(t.length>140||blocked.test(t))return;const key=[Math.round(r.left/3),Math.round(r.top/3),Math.round(r.width/3),Math.round(r.height/3)].join(':');if(rows.some(x=>x.key===key))return;const hasImage=!!target.querySelector?.('img')||target.tagName==='IMG';rows.push({key,x:r.left+r.width/2,y:r.top+r.height/2,top:r.top,area:r.width*r.height,hasImage});};
              [...panel.querySelectorAll('a[href],button,[role="button"],[role="menuitem"],[role="link"],img,[tabindex]')].forEach(add);[...panel.querySelectorAll('div,span')].filter(el=>getComputedStyle(el).cursor==='pointer').forEach(add);
              return rows.sort((a,b)=>(b.hasImage-a.hasImage)||a.top-b.top||b.area-a.area).slice(0,12).map(({x,y})=>({x,y}));
            }""")
            if slot>=len(points):break
            point=points[slot];await page.mouse.click(point["x"],point["y"])
            for _ in range(14):
                await page.wait_for_timeout(300)
                opened=[p for p in context.pages if p not in before and p!=page]
                for candidate in [page]+opened:
                    if urlsplit(candidate.url).hostname not in KWAI_HOSTS:continue
                    if await page_is_expected_owner_destination(candidate):return True
        except Exception:
            pass
        finally:
            for extra in list(context.pages):
                if extra not in before:
                    try:await extra.close()
                    except Exception:pass
    return False


async def inspect_existing_tab(context):
    guard=load_guard();page,authenticated,exact_link=await open_menu_page(context,guard)
    if not page:return {"chrome_connected":True,"authenticated_ui_detected":False,"exact_owner_menu_link":False,"menu_subtree_owner_match":False,"geometry_owner_match":False,"exact_owner_navigation":False,"identity_verified":False,"session_exported":False}
    try:subtree=await menu_subtree_owner_match(page) if authenticated else False
    finally:
        try:await page.close()
        except Exception:pass
    if authenticated and (exact_link or subtree):return {"chrome_connected":True,"authenticated_ui_detected":True,"exact_owner_menu_link":exact_link,"menu_subtree_owner_match":subtree,"geometry_owner_match":False,"exact_owner_navigation":False,"identity_verified":True,"session_exported":False}
    geometry=await menu_geometry_owner_match(context,guard) if authenticated else False
    if geometry:return {"chrome_connected":True,"authenticated_ui_detected":True,"exact_owner_menu_link":exact_link,"menu_subtree_owner_match":subtree,"geometry_owner_match":True,"exact_owner_navigation":True,"identity_verified":True,"session_exported":False}
    navigation=await guard.inspect_own_profile_navigation(context);nav_match=bool(navigation.get("account_menu_profile_navigation_matches"))
    if authenticated and nav_match:return {"chrome_connected":True,"authenticated_ui_detected":True,"exact_owner_menu_link":exact_link,"menu_subtree_owner_match":subtree,"geometry_owner_match":geometry,"exact_owner_navigation":True,"identity_verified":True,"session_exported":False}
    independent=await guard.inspect_profile_without_logout(context);independent_owner=bool(independent.get("profile_navigation_matches") is True and independent.get("profile_owner_control_visible") is True and independent.get("profile_login_controls_absent") is True)
    return {"chrome_connected":True,"authenticated_ui_detected":bool(authenticated or independent_owner),"exact_owner_menu_link":exact_link,"menu_subtree_owner_match":subtree,"geometry_owner_match":geometry,"exact_owner_navigation":bool(nav_match or independent_owner),"identity_verified":independent_owner,"session_exported":False}
