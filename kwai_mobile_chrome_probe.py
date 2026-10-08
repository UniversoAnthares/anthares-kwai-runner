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
            await page.screenshot(path=str(OUT/"mobile.png"),full_page=True)
        except Exception as e:
            result["error"]=str(e)[:300]
        (OUT/"results.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
        print("MOBILE_CHROME_PROBE="+json.dumps(result,ensure_ascii=False))
        await browser.close()
asyncio.run(main())
