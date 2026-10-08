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
            for path in ["/", "/pt-BR", "/pt-BR/upload", "/upload", "/creator", "/creator/upload", "/pt-BR/creator", "/pt-BR/creator/upload", "/studio", "/pt-BR/studio"]:
                try:
                    response=await page.goto("https://www.kwai.com"+path,wait_until="domcontentloaded",timeout=12000)
                    await page.wait_for_timeout(750)
                    result["routes"].append({"path":path,"status":response.status if response else None,"final_url":page.url,"title":await page.title(),"file_inputs":await page.locator('input[type="file"]').count(),"upload_text":await page.get_by_text(re.compile("upload|enviar|publicar|postar|carregar vídeo",re.I)).count()})
                except Exception as err:
                    result["routes"].append({"path":path,"error":str(err)[:120]})
            await page.goto("https://www.kwai.com/pt-BR",wait_until="domcontentloaded",timeout=15000)
            result["upload_candidates"]=await page.get_by_text(re.compile("upload|enviar|publicar|postar|carregar vídeo",re.I)).count()
            await page.screenshot(path=str(OUT/"mobile.png"),full_page=True)
        except Exception as e:
            result["error"]=str(e)[:300]
        (OUT/"results.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
        print("MOBILE_CHROME_PROBE="+json.dumps(result,ensure_ascii=False))
        await browser.close()
asyncio.run(main())
