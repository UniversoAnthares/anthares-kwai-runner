#!/usr/bin/env python3
"""Read-only recovery of a verified Kwai physical Android post's public URL.
This NEVER calls the publish path. An exact account and timestamp match is
mandatory before a share button can be opened. No URL means no ACK.
"""
from __future__ import annotations
import json, subprocess, os, pathlib, re, sys, time, urllib.request, xml.etree.ElementTree as ET

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import kwai_native_cortes as k

URL_RE=re.compile(r'https://(?:k\.kwai\.com/p/[A-Za-z0-9_-]+|www\.kwai\.com/@[A-Za-z0-9_.-]+/photo/[0-9]+)')
EVIDENCE=ROOT/'.state'/'kwai-memu-evidence'
ACK=ROOT/'.state'/'android-publish-ack.json'

def snapshot(serial,stage):
    root,path=k.dump(serial,stage)
    return [n for n in root.iter('node')],root

def meaningful(nodes):
    return [{'text':n.get('text') or n.get('content-desc') or '',
             'id':n.get('resource-id',''),'bounds':n.get('bounds','')} for n in nodes
            if (n.get('text') or n.get('content-desc')) and k.center(n.get('bounds',''))]

def select(nodes, words):
    return [n for n in nodes if k.center(n.get('bounds','')) and
            any(w in ((n.get('text') or '')+' '+(n.get('content-desc') or '')).casefold()
                for w in words)]

def clip_url(serial,jobid):
    # Use an ephemeral blank Chrome page only to read the Kwai-provided link.
    k.adb(serial,'shell','am','start','-a','android.intent.action.VIEW','-d','about:blank','-p','com.android.chrome',
          check=False,timeout=20)
    try:
        for attempt in range(5):
            time.sleep(2)
            nodes,_=snapshot(serial,jobid+'-proof-chrome-'+str(attempt))
            bars=[n for n in nodes if (n.get('resource-id') or '').endswith(':id/url_bar')
                  and k.center(n.get('bounds',''))]
            if not bars:continue
            k.tap(serial,bars[0])
            k.adb(serial,'shell','input','keyevent','279',check=False,timeout=15)
            time.sleep(1)
            nodes,_=snapshot(serial,jobid+'-proof-paste-'+str(attempt))
            val=' '.join((n.get('text') or '') for n in nodes
                         if (n.get('resource-id') or '').endswith(':id/url_bar'))
            urls=URL_RE.findall(val)
            if len(set(urls))==1:return urls[0]
        raise RuntimeError('kwai_share_link_clipboard_read_failed')
    finally:
        # Leave the personal Chrome process/tabs alive; return to Kwai.
        k.adb(serial,'shell','am','start','--activity-clear-top','-n',
              k.PKG+'/com.yxcorp.gifshow.homepage.HomeActivity',check=False,timeout=20)

def _supplementary_public_read(link, expected_account):
    """TinyFish first, public HTTPS backup. Never changes the physical ACK gate."""
    try:
        from tinyfish_public_probe import probe_public_page
        return probe_public_page(
            link, (expected_account,), fallback=True, timeout=6,
            allowed_hosts=("k.kwai.com", "www.kwai.com"),
        )
    except Exception:
        return {"provider": "tinyfish_fetch", "ok": False,
                "reason": "supplementary_read_unavailable"}


def recover(jid):
    clean=re.sub(r'[^A-Za-z0-9._-]+','_',jid)[-100:]
    ps=k.STATE/(clean+'.json')
    if not ps.exists():raise RuntimeError('kwai_native_verified_state_missing')
    state=json.loads(ps.read_text(encoding='utf-8'))
    ack=json.loads(ACK.read_text(encoding='utf-8')).get(jid,{})
    if ack.get('state')!='published_pending_ack':raise RuntimeError('kwai_not_pending_ack')
    if state.get('state')!='verified' or not state.get('publication_attempted'):
        raise RuntimeError('kwai_not_verified')
    expected_time=(state.get('profile_verification') or {}).get('post_time')
    expected_account=state.get('expected_account')
    if not expected_time or expected_account!='lucasrosalem':
        raise RuntimeError('kwai_exact_post_proof_missing')
    if (state.get('profile_verification') or {}).get('account')!=expected_account:
        raise RuntimeError('kwai_account_mismatch')

    serial=k.connect()
    # Check present screen first; let the caller report device sleep as P0.
    power=k.adb(serial,'shell','dumpsys','power',check=False,timeout=15).stdout or ''
    if 'mWakefulness=Asleep' in power:
        k.adb(serial,'shell','input','keyevent','224',check=False,timeout=15)
        time.sleep(3)
        power=k.adb(serial,'shell','dumpsys','power',check=False,timeout=15).stdout or ''
        if 'mWakefulness=Asleep' in power:
            raise RuntimeError('kwai_physical_device_asleep_proof_pending')

    latest=k.latest(serial,clean+'-proof',preserve_upload=True)
    if latest.get('account')!=expected_account or latest.get('post_time')!=expected_time:
        raise RuntimeError('kwai_public_post_identity_or_time_mismatch')
    nodes,_=snapshot(serial,clean+'-proof-available')
    share=[n for n in nodes if (n.get('resource-id') or '').endswith('/forward_button')
           and k.center(n.get('bounds','')) and n.get('clickable')=='true']
    if len(share)!=1:raise RuntimeError('kwai_share_button_unavailable')
    k.tap(serial,share[0])
    copy=[]
    for attempt in range(4):
        time.sleep(2)
        nodes,_=snapshot(serial,clean+'-proof-share-'+str(attempt))
        copy=select(nodes,('copiar link','copy link'))
        if len(copy)==1:break
    if len(copy)!=1:raise RuntimeError('kwai_copy_link_unavailable')
    k.tap(serial,copy[0])
    link=clip_url(serial,clean)
    if not URL_RE.fullmatch(link):raise RuntimeError('kwai_public_link_invalid')
    title=str(state.get('caption') or '').strip()
    digest=str(state.get('media_sha256') or '').lower()
    if len(title)<12 or not re.fullmatch(r'[a-f0-9]{64}',digest):
        raise RuntimeError('kwai_job_caption_or_media_digest_missing')
    # Android physically publishes; isolated MEmu verifies the resulting public
    # URL on Kwai by matching the target caption and author profile handle.
    env=os.environ.copy()
    env['KWAI_UP_ADB_SERIAL']=os.getenv('ANTHARES_MEMU_ADB_SERIAL','127.0.0.1:21543')
    env['ANTHARES_ADB']=str(k.ADB)
    verifier=ROOT/'tools'/'kwai_verify_public_post.py'
    p=subprocess.run([sys.executable,str(verifier),'--url',link,'--title',title,
        '--account',expected_account,'--display-name','Lucas Rosalem'],
        cwd=str(ROOT),env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
        text=True,timeout=145,check=False,
        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    matching=[line.split('KWAI_PUBLIC_LINK_VERIFIED=',1)[1]
              for line in (p.stdout or '').splitlines()
              if line.startswith('KWAI_PUBLIC_LINK_VERIFIED=')]
    if p.returncode!=0 or len(matching)!=1:
        raise RuntimeError('kwai_cross_device_public_identity_verification_failed')
    cross=json.loads(matching[0])
    if not (cross.get('ok') is True and cross.get('public_url')==link
            and cross.get('title_match') is True
            and cross.get('expected_account')==expected_account
            and cross.get('method')=='kwai_public_deeplink_title_and_author_profile_handle'):
        raise RuntimeError('kwai_cross_device_public_identity_mismatch')
    proof={
        'ok':True,'public_url':link,'expected_account':expected_account,
        'kind':'kwai_independent_cross_device_media_bound_v1',
        'verified_publication_job_id':jid,'caption':title,'media_sha256':digest,
        'cross_device_proof':cross,
        'published_post_time':expected_time,'verified_native_state':'verified',
        'verification_evidence':state.get('verification_evidence'),
        'method':'physical_profile_exact_account_timestamp_and_share_ui',
        'tinyfish_public_observation':_supplementary_public_read(link,expected_account),
        'checked_at':int(time.time())
    }
    directory=EVID/clean
    directory.mkdir(parents=True,exist_ok=True)
    path=directory/'public-link-proof.json'
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(proof,ensure_ascii=False,sort_keys=True),encoding='utf-8')
    temp.replace(path)
    print('KWAI_PHYSICAL_PROOF_RECOVERED '+link,flush=True)
    return 0

def main():
    if len(sys.argv)!=2:raise RuntimeError('usage: kwai_physical_public_proof.py JOB_ID')
    return recover(sys.argv[1])
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        print('KWAI_PHYSICAL_PROOF_PENDING '+type(exc).__name__+':'+str(exc)[:150],flush=True)
        raise SystemExit(75)
