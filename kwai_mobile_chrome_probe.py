import asyncio, json, pathlib, re
from playwright.async_api import async_playwright
OUT=pathlib.Path("kwai-mobile-chrome-results")
OUT.mkdir(exist_ok=True)
async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
        device=p.devices["Pixel 7"]
        ctx=await browser.new_context(**device,locale="pt-BR",timezone_id="America/Sao_Paulo")
        page=await ctx.new_page()
        result={"url":"https://www.kwai.com/pt-BR","mobile":True,"authenticated":False}
        try:
            resp=await page.goto(result["url"],wait_until="domcontentloaded",timeout=30000)
            await page.wait_for_timeout(4500)
            result["http_status"]=resp.status if resp else None
            result["final_url"]=page.url
            result["title"]=await page.title()
            result["buttons"]=(await page.locator("button").all_text_contents())[:60]
            result["links"]=(await page.locator("a").all_text_contents())[:60]
            result["upload_inputs"]=await page.locator('input[type="file"]').count()
            result["routes"]=[]
            for path in ["/","/pt-BR","/video/upload","/creators","/creators/create","/pt-BR/creators","/pt-BR/creators/create"]:
                try:
                    response=await page.goto("https://www.kwai.com"+path,wait_until="domcontentloaded",timeout=6500)
                    await page.wait_for_timeout(250)
                    result["routes"].append({"path":path,"status":response.status if response else None,"final_url":page.url,"title":await page.title(),"file_inputs":await page.locator('input[type="file"]').count(),"upload_text":await page.get_by_text(re.compile("upload|enviar|publicar|postar|carregar vídeo",re.I)).count(),"forms":await page.locator("form").count(),"buttons":(await page.locator("button").all_text_contents())[:40],"anchors":(await page.locator("a").all_text_contents())[:40],"iframes":await page.locator("iframe").count()})
                except Exception as err:
                    result["routes"].append({"path":path,"error":str(err)[:120]})
            await page.goto("https://www.kwai.com/pt-BR",wait_until="domcontentloaded",timeout=15000)
            result["page_forms"]=await page.locator("form").count()
            result["login_links"]=(await page.locator("a").all_text_contents())[:100]
            result["upload_candidates"]=await page.get_by_text(re.compile("upload|enviar|publicar|postar|carregar vídeo",re.I)).count()
            result["auth_discovery"]=[]
            for target in ["https://www.kwai.com/pt-BR","https://www.kwai.com/video/upload","https://www.kwai.com/pt-BR/creators/create","https://www.kwai.com/","https://www.kwai.com/@universo.anthares"]:
                try:
                    response=await page.goto(target,wait_until="domcontentloaded",timeout=12000)
                    await page.wait_for_timeout(1000)
                    item={"url":target,"status":response.status if response else None,"final_url":page.url,"title":await page.title(),"links":await page.locator("a").evaluate_all("(els)=>els.map(e=>({text:e.innerText.slice(0,80),href:e.href})).slice(0,80)"),"buttons":await page.locator("button").evaluate_all("(els)=>els.map(e=>({text:e.innerText.slice(0,80),title:e.title,aria:e.getAttribute('aria-label')})).slice(0,80)"),"inputs":await page.locator("input").evaluate_all("(els)=>els.map(e=>({type:e.type,placeholder:e.placeholder})).slice(0,30)"),"login_mentions":await page.get_by_text(re.compile("entrar|login|cadastro|sign in|log in|QR code",re.I)).count(),"upload_inputs":await page.locator('input[type="file"]').count()}
                    result["auth_discovery"].append(item)
                except Exception as err:
                    result["auth_discovery"].append({"url":target,"error":str(err)[:180]})
            result["interactive_discovery"]=[]
            for target in ["https://www.kwai.com/video/upload","https://www.kwai.com/","https://www.kwai.com/@universo.anthares"]:
                try:
                    await page.goto(target,wait_until="domcontentloaded",timeout=12000)
                    await page.wait_for_timeout(1800)
                    data=await page.evaluate("""() => ({
                        bodyText:document.body?.innerText?.slice(0,1800)||'',
                        clickable:[...document.querySelectorAll('[role=button],[onclick],[tabindex],svg')].slice(0,50).map(e=>({tag:e.tagName,role:e.getAttribute('role'),aria:e.getAttribute('aria-label'),text:e.textContent?.slice(0,80)})),
                        frames:[...document.querySelectorAll('iframe')].map(e=>e.src),
                        scripts:[...document.scripts].map(e=>e.src).filter(Boolean).slice(0,25),
                        nextData:!!document.querySelector('#__NEXT_DATA__')
                    })""")
                    result["interactive_discovery"].append({"url":target,**data})
                except Exception as err:
                    result["interactive_discovery"].append({"url":target,"error":str(err)[:140]})
            result["login_click_probe"]=[]
            for target in ["https://www.kwai.com/","https://www.kwai.com/video/upload","https://www.kwai.com/@universo.anthares"]:
                try:
                    await page.goto(target,wait_until="domcontentloaded",timeout=12000)
                    await page.wait_for_timeout(1300)
                    before=await page.locator('input').count()
                    actions=await page.evaluate("""() => [...document.querySelectorAll('button,a,[role=button]')].filter(e=>/login|log in|sign in|entrar|acessar|publicar|seguir|curtir/i.test((e.innerText||'')+' '+(e.getAttribute('aria-label')||''))).slice(0,12).map(e=>({tag:e.tagName,text:(e.innerText||'').slice(0,80),aria:e.getAttribute('aria-label')}))""")
                    clicked=False
                    for term in ["Entrar","Login","Log in","Sign in","Seguir"]:
                        locator=page.get_by_text(term,exact=True)
                        if await locator.count()>0:
                            try:
                                await locator.first.click(timeout=2000)
                                clicked=True
                                break
                            except Exception:
                                pass
                    await page.wait_for_timeout(900)
                    result["login_click_probe"].append({"url":target,"actions":actions,"clicked":clicked,"inputs_before":before,"inputs_after":await page.locator('input').count(),"dialogs":await page.locator('[role=dialog]').count(),"body_after":(await page.locator("body").inner_text())[:450]})
                except Exception as err:
                    result["login_click_probe"].append({"url":target,"error":str(err)[:150]})
            result["interaction_diagnostics"]=[]
            for target in ["https://www.kwai.com/","https://www.kwai.com/@universo.anthares"]:
                try:
                    await page.goto(target,wait_until="domcontentloaded",timeout=12000)
                    await page.wait_for_timeout(1600)
                    elements=await page.evaluate("""() => [...document.querySelectorAll('*')].filter(e=>['Seguir','Publicar','Abrir o Kwai'].includes((e.textContent||'').trim()) && e.children.length===0).slice(0,12).map(e=>({tag:e.tagName,text:e.textContent,outer:e.parentElement?.outerHTML.slice(0,450)}))""")
                    before=page.url
                    follow=page.get_by_text("Seguir",exact=True)
                    if await follow.count():
                        try:
                            await follow.first.click(timeout=2200)
                        except Exception:
                            pass
                    await page.wait_for_timeout(1600)
                    result["interaction_diagnostics"].append({"url":target,"elements":elements,"after_url":page.url,"changed_url":before!=page.url,"dialogs":await page.locator('[role=dialog]').count(),"inputs":await page.locator('input').count(),"visible_text":(await page.locator('body').inner_text())[:650]})
                except Exception as err:
                    result["interaction_diagnostics"].append({"url":target,"error":str(err)[:170]})
            result["social_dialog_probe"]=[]
            for target in ["https://www.kwai.com/","https://www.kwai.com/@universo.anthares"]:
                try:
                    await page.goto(target,wait_until="domcontentloaded",timeout=12000)
                    await page.wait_for_timeout(1500)
                    follow=page.get_by_text("Seguir",exact=True)
                    if await follow.count():
                        try:
                            await follow.first.click(timeout=1800,force=True)
                        except Exception:
                            await follow.first.evaluate("(el)=>el.click()")
                    await page.wait_for_timeout(1100)
                    info=await page.evaluate("""() => ({
                        visibleOverlays:[...document.querySelectorAll('[class*=social-dialog],[class*=SocialDialog]')].slice(0,8).map(e=>({html:e.outerHTML.slice(0,1400),text:e.innerText?.slice(0,350)})),
                        dialogText:[...document.querySelectorAll('[class*=Dialog],[class*=dialog],[class*=modal],[class*=Modal]')].map(e=>({className:e.className,text:e.innerText?.slice(0,250),html:e.outerHTML.slice(0,550)})).filter(x=>x.text).slice(0,15),
                        images:[...document.images].filter(e=>/qr|login|code/i.test(e.src+' '+e.alt)).map(e=>({src:e.src,alt:e.alt})).slice(0,10),
                        externalLinks:[...document.querySelectorAll('a')].filter(e=>/login|entrar|app/i.test(e.href+' '+e.textContent)).map(e=>({href:e.href,text:e.textContent.slice(0,70)})).slice(0,12)
                    })""")
                    result["social_dialog_probe"].append({"url":target,**info})
                except Exception as err:
                    result["social_dialog_probe"].append({"url":target,"error":str(err)[:150]})
            result["desktop_comparison"]=[]
            desktop=await browser.new_context(viewport={"width":1440,"height":900},locale="pt-BR",timezone_id="America/Sao_Paulo")
            dp=await desktop.new_page()
            for target in ["https://www.kwai.com/","https://www.kwai.com/video/upload","https://www.kwai.com/@universo.anthares"]:
                try:
                    response=await dp.goto(target,wait_until="domcontentloaded",timeout=14000)
                    await dp.wait_for_timeout(1700)
                    result["desktop_comparison"].append({"url":target,"status":response.status if response else None,"final_url":dp.url,"title":await dp.title(),"body":(await dp.locator("body").inner_text())[:650],"inputs":await dp.locator("input").count(),"file_inputs":await dp.locator('input[type=file]').count(),"login_mentions":await dp.get_by_text(re.compile("login|entrar|sign in|QR code",re.I)).count(),"links":(await dp.locator("a").all_text_contents())[:20]})
                except Exception as err:
                    result["desktop_comparison"].append({"url":target,"error":str(err)[:150]})
            result["desktop_login_probe"]=[]
            for target in ["https://www.kwai.com/","https://www.kwai.com/@universo.anthares"]:
                try:
                    await dp.goto(target,wait_until="domcontentloaded",timeout=13000)
                    await dp.wait_for_timeout(1300)
                    login=dp.get_by_text("Fazer login",exact=True)
                    count=await login.count()
                    if count:
                        await login.first.click(timeout=2500)
                    await dp.wait_for_timeout(1300)
                    result["desktop_login_probe"].append({"url":target,"login_controls":count,"after_url":dp.url,"inputs":await dp.locator('input').evaluate_all("(els)=>els.map(e=>({type:e.type,placeholder:e.placeholder})).slice(0,12)"),"dialogs":await dp.locator('[role=dialog]').count(),"body":(await dp.locator('body').inner_text())[:950],"qr_images":await dp.locator('img').evaluate_all("(els)=>els.filter(e=>/qr|code/i.test(e.src+' '+e.alt)).map(e=>e.src).slice(0,8)")})
                except Exception as err:
                    result["desktop_login_probe"].append({"url":target,"error":str(err)[:170]})
            await desktop.close()
            await page.screenshot(path=str(OUT/"mobile.png"),full_page=True)
        except Exception as e:
            result["error"]=str(e)[:300]
        (OUT/"results.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
        print("MOBILE_CHROME_PROBE="+json.dumps(result,ensure_ascii=False))
        await browser.close()
asyncio.run(main())
