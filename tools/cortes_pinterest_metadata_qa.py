#!/usr/bin/env python3
"""Device-scoped Pinterest QA: autonomous 404 recheck + transcript-based clip metadata.
Runs under the existing authenticated hidden Windows task, does not publish,
mutate UNCERTAIN rows, or access personal Chrome tabs.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.cortes_pinterest_browser_local import call,OWNER,TARGET,qa_incident
from anthares_publisher.editorial import STRATEGIC_POLICY,require_strategic_master,SUFFIX

CACHE=ROOT/'.pinterest-transcripts'
WHISPER=None

def approved_media(url):
    p=urlparse(str(url or ''))
    return (p.scheme=='https' and p.hostname in ('anthares.us','www.anthares.us')
      and not p.username and not p.password and not p.query and not p.fragment
      and p.path.startswith('/wp-content/uploads/anthares-clips/')
      and p.path.lower().endswith('.mp4'))

def media_status(url):
    if not approved_media(url):
        return None
    for method in ('HEAD','GET'):
        req=urllib.request.Request(url,method=method,
            headers={'User-Agent':'CortesPinterestQAMedia24h/1.0',
                     **({'Range':'bytes=0-0'} if method=='GET' else {})})
        try:
            with urllib.request.urlopen(req,timeout=17) as res:
                code=int(res.status)
                if code in (200,206):
                    return 200
        except urllib.error.HTTPError as e:
            if e.code==404:return 404
            if e.code not in (405,501):return None
        except (TimeoutError,OSError):return None
    return None

def media_qa():
    out=call('qa-media-pending',{'target_key':TARGET,'owner':OWNER})
    if not out.get('ok'):raise RuntimeError('PINTEREST_QA_24H_READ_FAILED')
    count=0
    for j in out.get('jobs') or []:
        url=str(j.get('media_url') or '')
        code=media_status(url)
        if code not in (200,404):
            qa_incident('PINTEREST_MEDIA_QA_HEAD_UNAVAILABLE')
            continue
        result=call('qa-media-result',{'target_key':TARGET,'owner':OWNER,
                'id':j['id'],'media_url':url,'http_status':code})
        if not result.get('ok'):
            qa_incident('PINTEREST_MEDIA_QA_CAS_FAILED')
            continue
        st=(result.get('job') or {}).get('status')
        ev=(result.get('job') or {}).get('confirmation_evidence') or {}
        print(json.dumps({'qa':'MEDIA_24H_CHECK','status':st,
                          'kind':ev.get('kind'),'id':j['id']},ensure_ascii=False),flush=True)
        count+=1
    return count

def transcript(url):
    global WHISPER
    if not approved_media(url):raise RuntimeError('PINTEREST_ASR_MEDIA_DENIED')
    CACHE.mkdir(parents=True,exist_ok=True)
    filepath=CACHE/(hashlib.sha256(url.encode()).hexdigest()+'.txt')
    if filepath.exists():
        return filepath.read_text(encoding='utf8')
    from faster_whisper import WhisperModel
    if WHISPER is None:
        # Local model cache only: QA must not silently download new models.
        WHISPER=WhisperModel('small',device='cpu',compute_type='int8',local_files_only=True)
    lines,meta=WHISPER.transcribe(url,language='pt',beam_size=3,vad_filter=True)
    text=' '.join(' '.join(x.text.strip().split()) for x in lines).strip()
    if len(text)<95 or len(text)>14000:
        raise RuntimeError('PINTEREST_ASR_NOT_USEFUL')
    filepath.write_text(text,encoding='utf8')
    return text

def strategic_metadata(text,source_title,segment_id):
    prompt=('Você é editor de cortes de debates literários e filosóficos em português. '
      'Leia somente a TRANSCRIÇÃO do trecho. Crie um título ORIGINAL, inteligente, '
      'específico deste argumento e chamativo sem sensacionalismo. '
      'NÃO copie o título da live nem acrescente fatos não ditos. '
      'Retorne SOMENTE objeto JSON com title (português, 30 a 72 caracteres, sem marca), '
      'keywords (4 expressões com conteúdo do trecho) e hashtags '
      '(3 tags temáticas começando com #, sem espaços).\n'
      'CONTEXTO GERAL DA LIVE (não serve como título): '+source_title+'\n'
      'TRECHO TRANSCRITO: '+text[:2200])
    data=json.dumps({'model':'qwen2.5:3b','prompt':prompt,'stream':False,
                     'format':'json','options':{'temperature':0.22,'num_predict':230}},
                     ensure_ascii=False).encode('utf8')
    req=urllib.request.Request('http://127.0.0.1:11434/api/generate',
             data=data,headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=90) as rsp:
        answer=json.loads(json.load(rsp).get('response','{}'))
    headline=' '.join(str(answer.get('title') or '').split()).strip().strip('"').strip('.,;:')
    if headline.endswith(SUFFIX):
        headline=headline[:-len(SUFFIX)].strip()
    title=headline[:100-len(SUFFIX)].rstrip(' ,.;:')+SUFFIX
    if not (40<=len(title)<=100) or headline.casefold() in source_title.casefold():
        raise RuntimeError('PINTEREST_CONTEXTUAL_TITLE_INVALID')
    words=answer.get('keywords')
    tags=answer.get('hashtags')
    if not isinstance(words,list) or not isinstance(tags,list):
        raise RuntimeError('PINTEREST_CONTEXTUAL_KEYWORDS_INVALID')
    words=list(dict.fromkeys(str(v).strip() for v in words if isinstance(v,str)
                             and 3<=len(v.strip())<=65))[:9]
    tags=list(dict.fromkeys(str(v).strip() for v in tags if isinstance(v,str)
                            and re.fullmatch(r'#[\wÀ-ÿ]{2,40}',v.strip())))[:9]
    description=('Neste corte, o debate aborda: '+text[:380].strip()+
                 '\nVeja também: www.anthares.us')
    description=description[:500].rstrip()
    data={'title':title,'description':description,'keywords':words,
          'hashtags':tags,'segment_id':segment_id,'editorial_policy':STRATEGIC_POLICY}
    require_strategic_master(data)
    return data

def metadata_qa(max_clips=3):
    processed=0
    after=''
    while processed < max_clips:
        out=call('metadata-pending',{'target_key':TARGET,'owner':OWNER,'after_id':after})
        if not out.get('ok'):raise RuntimeError('PINTEREST_QA_METADATA_READ_FAILED')
        jobs=out.get('jobs') or []
        if not jobs:break
        for row in jobs:
            after=row['id']
            if not approved_media(row.get('media_url')):
                qa_incident('PINTEREST_QA_UNTRUSTED_MEDIA')
                continue
            if media_status(row['media_url'])!=200:
                qa_incident('PINTEREST_QA_TRANSCRIPT_MEDIA_UNAVAILABLE')
                continue
            try:
                text=transcript(row['media_url'])
                d=strategic_metadata(text,str(row.get('source_title') or ''),
                                     str(row.get('segment_id') or ''))
                update=call('metadata-enrich',{'target_key':TARGET,'owner':OWNER,
                    'id':row['id'],'segment_id':row['segment_id'],
                    'original_title':row['source_title'],
                    'title':d['title'],'description':d['description'],
                    'keywords':d['keywords'],'hashtags':d['hashtags'],
                    'transcript_hash':hashlib.sha256(text.encode('utf8')).hexdigest()})
                if not update.get('ok'):
                    raise RuntimeError('PINTEREST_QA_METADATA_CAS_REJECTED')
                processed+=1
                print(json.dumps({'qa':'METADATA_REPAIRED','id':row['id'],
                     'title':d['title']},ensure_ascii=False),flush=True)
            except (RuntimeError,ValueError,KeyError,urllib.error.URLError,OSError) as e:
                qa_incident('PINTEREST_METADATA_'+type(e).__name__.upper())
                print(json.dumps({'qa':'METADATA_BLOCKED','id':row['id'],
                       'kind':type(e).__name__}),flush=True)
            if processed>=max_clips:break
        if len(jobs)<4:break
    return processed

def main():
    if not os.getenv('ANTHARES_DEVICE_TOKEN','').strip():
        raise RuntimeError('PINTEREST_QA_DEVICE_AUTH_MISSING')
    from argparse import ArgumentParser
    p=ArgumentParser()
    p.add_argument('--media-only',action='store_true')
    p.add_argument('--titles-only',action='store_true')
    p.add_argument('--max-clips',type=int,default=3)
    args=p.parse_args()
    if args.max_clips<1 or args.max_clips>6:raise RuntimeError('QA_BATCH_LIMIT_INVALID')
    m=0 if args.titles_only else media_qa()
    t=0 if args.media_only else metadata_qa(args.max_clips)
    print(json.dumps({'qa':'DONE','media_checked':m,'titles_repaired':t}),flush=True)
    return 0

if __name__=='__main__':
    try:
        sys.exit(main())
    except Exception as e:
        qa_incident('PINTEREST_QA_PIPELINE_'+type(e).__name__.upper())
        print(json.dumps({'qa':'BLOCKED','kind':type(e).__name__}))
        sys.exit(2)
