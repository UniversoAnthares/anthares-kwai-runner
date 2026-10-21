#!/usr/bin/env python3
"""Read-only Threads owner proof through isolated Anthares-browser control API."""
import json
import os
import time
import urllib.request

BASE="http://127.0.0.1:18080"
def post(route, payload):
    request=urllib.request.Request(
        BASE+route, data=json.dumps(payload).encode("utf-8"),method="POST",
        headers={"Authorization":"Bearer "+os.environ["CONTROL"],
                 "Content-Type":"application/json"})
    with urllib.request.urlopen(request, timeout=40) as result:
        return json.load(result)

try:
    post("/navigate",{"url":"https://www.threads.com/","wait_ms":9000})
    time.sleep(5)
    expression="""(() => {
      const links=[...document.querySelectorAll('a[href]')];
      const owner=links.some(a=>/^\/@universoanthares\/?$/.test(a.getAttribute('href')||''));
      const composer=!!document.querySelector('[contenteditable=true],[aria-label^="Campo de texto vazio"]');
      const login=!!document.querySelector('input[type=password]') ||
           /entrar no threads|log in to threads|fazer login no threads/i.test((document.body?.innerText||'').slice(0,1300));
      return {host:location.hostname,owner,composer,login};
    })()"""
    data=post("/evaluate",{"expression":expression}).get("result",{}).get("value") or {}
    verified=data.get("host") in ("www.threads.com","threads.com") and data.get("owner") is True and data.get("composer") is True and data.get("login") is False
    print("CLOUD_THREADS_OWNER_LINK="+str(data.get("owner",False)).lower())
    print("CLOUD_THREADS_COMPOSER="+str(data.get("composer",False)).lower())
    print("CLOUD_THREADS_LOGIN_PROMPT="+str(data.get("login",True)).lower())
    print("CLOUD_THREADS_AUTH="+("PROVEN" if verified else "NOT_PROVEN"))
except Exception as exc:
    print("CLOUD_THREADS_AUTH=NOT_PROVEN")
    print("CLOUD_THREADS_DIAGNOSTIC="+type(exc).__name__)
