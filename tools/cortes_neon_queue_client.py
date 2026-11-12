#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import time
import pathlib
import urllib.error
import urllib.parse
import urllib.request
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

BASE=(os.getenv('CORTES_QUEUE_URL') or 'https://anthares-remote-primary.vercel.app/api/cortes-queue').strip()
TOKEN=os.getenv('ANTHARES_DEVICE_TOKEN','').strip()
DEVICE=os.getenv('ANTHARES_DEVICE_ID','DESKTOP-FTDK0HP').strip()


_NEON='https://br-crimson-unit-b89nau08-cortesqueue.compute.c-14.us-east-1.aws.neon.tech/'
_PHYSICAL_KEY=pathlib.Path(os.getenv('ANTHARES_PHYSICAL_EXECUTOR_KEY',r'D:\AntharesWork\anthares-clipper\local-control\executor-private-current.pem'))
ACCOUNT=os.getenv('KWAI_EXPECTED_ACCOUNT','lucasrosalem').strip().lstrip('@').lower()
if ACCOUNT not in ('lucasrosalem','universoanthares'):raise RuntimeError('KWAI_ACCOUNT_NOT_ALLOWED')
_TARGET='kwai:'+ACCOUNT
_ACTIONS={'stats':'kwai-physical-stats','lease':'kwai-lease','start':'kwai-start','confirm':'kwai-confirm','fail':'kwai-fail','renew':'kwai-renew','historical':'kwai-historical-resolve','no-post-repair':'kwai-physical-repair-no-post','unproven':'kwai-unproven'}

def call(action: str, payload: dict | None=None, method: str='POST') -> dict:
    if BASE.rstrip('/')!=_NEON.rstrip('/'):
        raise RuntimeError('KWAI_PHYSICAL_NEON_CANONICAL_URL_REQUIRED')
    if action not in _ACTIONS or method!='POST':
        raise RuntimeError('KWAI_PHYSICAL_NEON_ACTION_INVALID')
    body={'target_key':_TARGET,'expected_account':ACCOUNT,**(payload or {})}
    if body.get('target_key')!=_TARGET or body.get('expected_account')!=ACCOUNT:
        raise RuntimeError('KWAI_PHYSICAL_TARGET_MISMATCH')
    if action=='lease':
        body={'lease_seconds':min(3600,max(90,int(body.pop('lease_seconds',body.pop('ttl_seconds',3600))))),**body}
    raw=json.dumps(body,ensure_ascii=False,separators=(',',':')).encode('utf8')
    endpoint=_NEON+'?'+urllib.parse.urlencode({'action':_ACTIONS[action]})
    ts=str(int(time.time()))
    nonce=secrets.token_hex(16)
    path='/?'+urllib.parse.urlencode({'action':_ACTIONS[action]})
    signed=(ts+'\nPOST\n'+path+'\n'+nonce+'\n').encode('utf8')+raw
    private=serialization.load_pem_private_key(_PHYSICAL_KEY.read_bytes(),password=None)
    signature=private.sign(signed,padding.PKCS1v15(),hashes.SHA256())
    import base64
    request=urllib.request.Request(endpoint,data=raw,method='POST',headers={
        'Content-Type':'application/json','Accept':'application/json',
        'X-Anthares-Device':'DESKTOP-FTDK0HP',
        'X-Anthares-Executor-Timestamp':ts,
        'X-Anthares-Executor-Nonce':nonce,
        'X-Anthares-Executor-Signature':base64.b64encode(signature).decode('ascii'),
        'User-Agent':'AntharesPhysicalNeon/1'})
    try:
        with urllib.request.urlopen(request,timeout=45) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        try: result=json.loads(exc.read().decode('utf-8'))
        except (ValueError,UnicodeError): result={'ok':False,'error':'HTTP_'+str(exc.code)}
        result['http_status']=exc.code
        return result


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('action',choices=['stats','lease','start','confirm','fail','renew','historical','job'])
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
