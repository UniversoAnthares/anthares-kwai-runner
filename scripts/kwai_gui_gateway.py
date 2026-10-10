#!/usr/bin/env python3
"""Private cookie-authenticated noVNC reverse proxy; no HTTP Basic browser dialog."""
import asyncio, hashlib, hmac, os, secrets, time
from aiohttp import web, ClientSession, WSMsgType

PASSWORD=os.environ["REMOTE_PASSWORD"]
USER=os.environ.get("REMOTE_USER","anthares")
KEY=secrets.token_bytes(32)
UPSTREAM="http://127.0.0.1:6081"
COOKIE="anthares_gui"
def signed_cookie():
    ts=str(int(time.time())//3600)
    sig=hmac.new(KEY,ts.encode(),hashlib.sha256).hexdigest()
    return ts+"."+sig
def valid(request):
    value=request.cookies.get(COOKIE,"")
    try:
        ts,sig=value.split(".",1)
        return abs(int(time.time())//3600-int(ts))<=1 and hmac.compare_digest(sig,hmac.new(KEY,ts.encode(),hashlib.sha256).hexdigest())
    except (ValueError,TypeError): return False
async def login(request):
    if request.method=="GET":
        return web.Response(text='<!doctype html><html lang="pt-br"><meta charset="utf-8"><title>Anthares Android</title><form method="post"><label>Usuário <input name="user" autocomplete="username"></label><label>Senha <input type="password" name="password" autocomplete="current-password"></label><button>Entrar</button></form></html>',content_type="text/html",headers={"Cache-Control":"no-store"})
    data=await request.post()
    if not (hmac.compare_digest(str(data.get("user","")),USER) and hmac.compare_digest(str(data.get("password","")),PASSWORD)):
        return web.Response(status=403,text="Credenciais inválidas")
    response=web.HTTPFound("/vnc.html?autoconnect=1&resize=scale")
    response.set_cookie(COOKIE,signed_cookie(),httponly=True,secure=True,samesite="Lax",max_age=7200)
    raise response
async def proxy(request):
    if not valid(request):
        if request.path=="/health": return web.Response(status=401)
        raise web.HTTPFound("/login")
    target=UPSTREAM+request.rel_url.path_qs
    if request.headers.get("Upgrade","").lower()=="websocket":
        client=web.WebSocketResponse(heartbeat=25)
        await client.prepare(request)
        async with ClientSession() as session:
            async with session.ws_connect(target,heartbeat=25) as remote:
                async def downstream():
                    async for msg in client:
                        if msg.type==WSMsgType.BINARY: await remote.send_bytes(msg.data)
                        elif msg.type==WSMsgType.TEXT: await remote.send_str(msg.data)
                        elif msg.type in (WSMsgType.CLOSE,WSMsgType.ERROR): break
                async def upstream():
                    async for msg in remote:
                        if msg.type==WSMsgType.BINARY: await client.send_bytes(msg.data)
                        elif msg.type==WSMsgType.TEXT: await client.send_str(msg.data)
                        elif msg.type in (WSMsgType.CLOSE,WSMsgType.ERROR): break
                tasks=[asyncio.create_task(downstream()),asyncio.create_task(upstream())]
                await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
                for task in tasks: task.cancel()
        return client
    async with ClientSession() as session:
        async with session.get(target,allow_redirects=False) as upstream:
            body=await upstream.read()
            headers={k:v for k,v in upstream.headers.items() if k.lower() not in ("content-length","transfer-encoding","connection","content-encoding")}
            return web.Response(body=body,status=upstream.status,headers=headers)
app=web.Application()
app.router.add_route("*","/login",login)
app.router.add_route("*","/{tail:.*}",proxy)
web.run_app(app,host="127.0.0.1",port=6080,access_log=None)
