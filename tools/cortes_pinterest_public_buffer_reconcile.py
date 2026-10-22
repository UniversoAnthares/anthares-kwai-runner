#!/usr/bin/env python3
"""Recover a Buffer-scheduled Pinterest Pin using independent live readback.

Never creates a Pin, never retries a Buffer mutation and never alters an
UNCERTAIN row without exact source video duration + board/account proof.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.cortes_pinterest_browser_local import call, OWNER, TARGET

def command(args: list[str], timeout: int=65):
    flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                     timeout=timeout,text=True,encoding='utf8',
                     errors='replace',creationflags=flags,cwd=str(ROOT))
    if p.returncode!=0:
        raise RuntimeError('PINTEREST_PUBLIC_VERIFIER_FAILED')
    return p.stdout.strip()

def source_duration(url: str) -> int:
    parsed=urlparse(url)
    if(parsed.scheme!='https' or parsed.hostname!='anthares.us' or
       parsed.username or parsed.password or parsed.query or parsed.fragment or
       not parsed.path.startswith('/wp-content/uploads/anthares-clips/') or
       not parsed.path.endswith('.mp4')):
        raise RuntimeError('PINTEREST_SOURCE_IDENTITY_INVALID')
    data=json.loads(command(['ffprobe','-v','error','-show_entries',
              'format=duration','-of','json',url]))
    duration=round(float((data.get('format') or {})['duration'])*1000)
    if not 10000<=duration<=90000:
        raise RuntimeError('PINTEREST_SOURCE_DURATION_INVALID')
    return duration

def verify(pin_id: str, source_url: str):
    if not re.fullmatch(r'[0-9]{10,25}',pin_id):
        raise RuntimeError('PINTEREST_PIN_ID_INVALID')
    src_ms=source_duration(source_url)
    value=json.loads(command(['node',str(ROOT/'tools'/'cortes_pinterest_public_pin_readback.mjs'),pin_id]))
    pub_ms=int(value.get('public_duration_ms') or 0)
    if(value.get('ok') is not True or value.get('pin_id')!=pin_id or
       value.get('verified_account')!='lucasyahn' or
       value.get('board_id')!='819514532133906920' or
       value.get('verified_public_board') is not True or
       pub_ms<10000 or abs(src_ms-pub_ms)>120):
        raise RuntimeError('PINTEREST_PUBLIC_SOURCE_MISMATCH')
    return src_ms,pub_ms

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--job-id',required=True)
    p.add_argument('--buffer-post-id',required=True)
    p.add_argument('--pin-id',required=True)
    p.add_argument('--source-url',required=True)
    p.add_argument('--commit',action='store_true')
    a=p.parse_args()
    if not re.fullmatch(r'cortes-fanout-pinterest-[a-f0-9]{32}',a.job_id):
        raise RuntimeError('PINTEREST_JOB_ID_INVALID')
    if not re.fullmatch(r'[a-f0-9]{24}',a.buffer_post_id):
        raise RuntimeError('PINTEREST_BUFFER_ID_INVALID')
    src_ms,pub_ms=verify(a.pin_id,a.source_url)
    preview={'ok':True,'verified_pin':'https://br.pinterest.com/pin/'+a.pin_id+'/',
             'source_duration_ms':src_ms,'public_duration_ms':pub_ms,
             'network_readback':True,'neon_write':False}
    if not a.commit:
        print(json.dumps(preview))
        return 0
    if not os.getenv('ANTHARES_DEVICE_TOKEN','').strip():
        raise RuntimeError('PINTEREST_DEVICE_AUTH_MISSING')
    value=call('reconcile-buffer',{'target_key':TARGET,'owner':OWNER,'id':a.job_id,
       'buffer_post_id':a.buffer_post_id,'pin_id':a.pin_id,
       'public_url':preview['verified_pin'],'source_media_url':a.source_url,
       'source_duration_ms':src_ms,'public_duration_ms':pub_ms,
       'board_id':'819514532133906920','verified_account':'lucasyahn',
       'verified_public_board':True})
    if not value.get('ok') or (value.get('job') or {}).get('status')!='confirmed':
        raise RuntimeError('PINTEREST_BUFFER_PUBLIC_CAS_REJECTED')
    preview['neon_write']=True
    preview['job_id']=a.job_id
    print(json.dumps(preview))
    return 0

if __name__=='__main__':
    try:
        sys.exit(main())
    except (RuntimeError,ValueError,KeyError,subprocess.TimeoutExpired) as exc:
        print(json.dumps({'ok':False,'reason':str(exc)[:95]}))
        sys.exit(2)
