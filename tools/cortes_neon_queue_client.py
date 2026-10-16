#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE=(os.getenv('CORTES_QUEUE_URL') or (os.getenv('ANTHARES_CONTROL_URL','https://anthares-remote-primary.vercel.app').rstrip('/')+'/api/cortes-queue')).strip()
TOKEN=os.getenv('ANTHARES_DEVICE_TOKEN','').strip()
DEVICE=os.getenv('ANTHARES_DEVICE_ID','DESKTOP-FTDK0HP').strip()


def call(action: str, payload: dict | None=None, method: str='POST') -> dict:
    if not TOKEN:
        raise RuntimeError('ANTHARES_DEVICE_TOKEN missing')
    url=BASE+'?'+urllib.parse.urlencode({'action':action})
    data=None if payload is None else json.dumps(payload,separators=(',',':')).encode()
    req=urllib.request.Request(url,data=data,method=method,headers={
        'Authorization':'Bearer '+TOKEN,
        'X-Anthares-Device':DEVICE,
        'Content-Type':'application/json',
        'User-Agent':'AntharesCortesQueueClient/1.0',
    })
    try:
        with urllib.request.urlopen(req,timeout=45) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raw=e.read().decode(errors='replace')
        try: body=json.loads(raw)
        except Exception: body={'ok':False,'error':raw or f'http_{e.code}'}
        body.setdefault('http_status',e.code)
        return body


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('action',choices=['enqueue','lease','start','confirm','fail','reconcile','retention','job'])
    ap.add_argument('--json',default='{}',help='JSON payload or @file')
    ap.add_argument('--id',default='')
    args=ap.parse_args()
    if args.action=='job':
        if not args.id: raise SystemExit('--id required')
        # job is GET but still authenticated.
        if not TOKEN: raise RuntimeError('ANTHARES_DEVICE_TOKEN missing')
        url=BASE+'?'+urllib.parse.urlencode({'action':'job','id':args.id})
        req=urllib.request.Request(url,headers={'Authorization':'Bearer '+TOKEN,'X-Anthares-Device':DEVICE,'User-Agent':'AntharesCortesQueueClient/1.0'})
        with urllib.request.urlopen(req,timeout=30) as r: out=json.loads(r.read().decode())
    else:
        raw=open(args.json[1:],encoding='utf-8-sig').read() if args.json.startswith('@') else args.json
        out=call(args.action,json.loads(raw))
    print(json.dumps(out,ensure_ascii=False,separators=(',',':')))
    return 0 if out.get('ok') else 2

if __name__=='__main__':
    raise SystemExit(main())
