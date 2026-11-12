#!/usr/bin/env python3
"""No-retry Kwai reconciliation sweep. All video decoding is in RAM."""
from __future__ import annotations
import datetime, hashlib, json, os, pathlib, re, subprocess, sys, time, urllib.request
import xml.etree.ElementTree as ET

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
ACCOUNT=os.environ.get('KWAI_EXPECTED_ACCOUNT','').strip().lstrip('@').lower()
assert ACCOUNT in ('lucasrosalem','universoanthares')
PKG='kwai.lite.video' if ACCOUNT=='lucasrosalem' else 'com.kwai.video'
ADB=os.environ.get('ANTHARES_ADB',r'C:\Users\Lucas\.kwai-up\platform-tools\adb.exe')
SERIAL=os.environ.get('ANTHARES_PHYSICAL_ADB_SERIAL','993fce720408')
PORT=os.environ.get('ANTHARES_PHYSICAL_ADB_PORT','5037')
TEMP='/data/local/tmp/anthares-cortes-unproven-auth-profile.xml'

def adb(*args,timeout=15,check=True):
 p=subprocess.run([ADB,'-P',PORT,'-s',SERIAL,*args],capture_output=True,
                  timeout=timeout)
 if check and p.returncode:raise RuntimeError('ANDROID_READONLY_AUTH_UNAVAILABLE')
 return p

def xml():
 try:
  adb('shell','uiautomator','dump',TEMP,timeout=23)
  p=adb('exec-out','cat',TEMP,timeout=12)
  return ET.fromstring(p.stdout)
 except (ET.ParseError,subprocess.TimeoutExpired) as exc:
  raise RuntimeError('ANDROID_AUTH_UI_DUMP_FAILED') from exc

def signed_in_account():
 # Profile is opened in the already authenticated Kwai app, never Chrome guest.
 # The same ADB device lease is held by the daemon during this procedure.
 activity=PKG+'/com.yxcorp.gifshow.homepage.HomeActivity'
 p=adb('shell','am','start','--activity-reorder-to-front','-n',activity,
       timeout=15,check=False)
 if p.returncode:return False
 time.sleep(1)
 root=xml()
 key=PKG+'.basis:id/id_home_bottom_tab_me'
 tabs=[x for x in root.iter('node') if x.get('resource-id')==key and
       x.get('enabled')=='true']
 if len(tabs)!=1:return False
 m=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',tabs[0].get('bounds',''))
 if not m:return False
 a,b,c,d=map(int,m.groups())
 if adb('shell','sh','/data/local/tmp/anthares-hid-tap.sh',
        str((a+c)//2),str((b+d)//2),timeout=15,check=False).returncode:return False
 time.sleep(1)
 for attempt in (0,1):
  root=xml()
  ids=[(n.get('text') or '').strip().lstrip('@').lower()
       for n in root.iter('node')
       if n.get('resource-id') in (PKG+'.basis_extension:id/tv_user_id',
                                      PKG+'.basis:id/tv_user_id')]
  if len(ids)==1:return ids[0]==ACCOUNT
  if attempt==0:
   script='/data/local/tmp/anthares-kwai-profile-scroll.sh'
   if adb('shell','sh',script,timeout=18,check=False).returncode:return False
   time.sleep(1)
 return False

def source_hash(url):
 h=hashlib.sha256();total=0
 with urllib.request.urlopen(url,timeout=15) as response:
  while True:
   chunk=response.read(512*1024)
   if not chunk:break
   total+=len(chunk)
   if total>70*1024*1024:raise ValueError('SOURCE_OVERSIZED')
   h.update(chunk)
 if total<2048:raise ValueError('SOURCE_EMPTY')
 return h.hexdigest()

def compare_in_memory(source_url,public_url):
 import cv2
 from kwai_public_feed_proof import feature_inliers
 features=[];durations=[]
 sift=cv2.SIFT_create(nfeatures=500)
 for u in (source_url,public_url):
  video=cv2.VideoCapture(u)
  try:
   if not video.isOpened():raise ValueError('MEDIA_STREAM_UNAVAILABLE')
   fps=video.get(cv2.CAP_PROP_FPS)
   count=video.get(cv2.CAP_PROP_FRAME_COUNT)
   duration=count/fps if fps else 0
   if not 4<=duration<=1500:raise ValueError('MEDIA_DURATION_INVALID')
   frames=[]
   for fraction in (.12,.38,.64,.90):
    video.set(cv2.CAP_PROP_POS_MSEC,duration*fraction*1000)
    ok,img=video.read()
    if not ok:raise ValueError('MEDIA_FRAME_NOT_DECODED')
    h,w=img.shape[:2];scale=350/max(w,h)
    gray=cv2.cvtColor(cv2.resize(img,(max(1,int(w*scale)),max(1,int(h*scale)))),
                      cv2.COLOR_BGR2GRAY)
    frames.append(sift.detectAndCompute(gray,None))
   features.append(frames);durations.append(duration)
  finally:video.release()
 if abs(durations[0]-durations[1])>2:raise ValueError('MEDIA_DURATION_MISMATCH')
 scores=[feature_inliers(a,b) for a,b in zip(features[0],features[1])]
 if not all(x>=75 for x in scores):raise ValueError('FOUR_FRAME_MEDIA_MISMATCH')
 return scores,durations

def check(job):
 from cortes_neon_queue_client import call
 from kwai_public_feed_proof import get_feed
 jid=str(job['id']);started=datetime.datetime.fromisoformat(
     str(job['publication_started_at']).replace('Z','+00:00'))
 started_ms=int(started.timestamp()*1000)
 source=str(job.get('source_url') or '')
 if not source.startswith('https://anthares.us/wp-content/uploads/anthares-clips/') or not source.endswith('.mp4'):
  print('UNPROVEN_SKIP_SOURCE_URL_NOT_TRUSTED',jid,flush=True);return
 age_minutes=(time.time()*1000-started_ms)/60000
 last_error='none';feed=None;logged=False
 for attempt in (1,2):
  try:
   logged=signed_in_account()
   if not logged:raise RuntimeError('AUTHENTICATED_ACCOUNT_NOT_PROVEN')
   feed=get_feed(60)
   break
  except Exception as e:
   last_error=type(e).__name__+':'+str(e)[:110]
   print('KWAI_UNPROVEN_SCAN_RETRY',jid,attempt,last_error,flush=True)
   if attempt==1:time.sleep(2)
 if feed is None:
  if age_minutes<90:
   print('KWAI_UNPROVEN_SCAN_DEFERRED_GRACE',jid,round(age_minutes,1),flush=True);return
  proof={'kind':'kwai_bounded_public_scan_discard_v1','job_id':jid,
         'account':ACCOUNT,'scanned_at_epoch_ms':int(time.time()*1000),
         'confirmed_public_media':False,'result':'scan_failed_bounded',
         'attempt_count':2,'scan_error':last_error}
  out=call('unproven',{'mode':'discard','id':jid,'proof':proof})
  print('KWAI_UNPROVEN_DISCARDED_AFTER_SCAN_FAILURE',jid,
        out.get('ok'),out.get('error',''),flush=True)
  return
 oldest=min(x['created_ms'] for x in feed)
 newest=max(x['created_ms'] for x in feed)
 candidates=[x for x in feed if started_ms-8*60000<=x['created_ms']<=started_ms+18*60000
             and x.get('account')==ACCOUNT]
 if len(candidates)==1:
  cand=candidates[0]
  try:
   local=ROOT/'.state'/'kwai-native-cortes'/(jid+'.json')
   native=json.loads(local.read_text(encoding='utf8'))
   if native.get('job_id')!=jid or native.get('expected_account')!=ACCOUNT:
    raise ValueError('NATIVE_JOB_ACCOUNT_MISMATCH')
   expected=native.get('media_sha256')
   sha=source_hash(source)
   if sha!=expected:raise ValueError('SOURCE_NATIVE_HASH_MISMATCH')
   scores,durations=compare_in_memory(source,cand['media_url'])
   photo=str(cand['photo_id'])
   proof={'kind':'kwai_logged_source_to_public_four_frame_v1','job_id':jid,
          'account':ACCOUNT,'authenticated_identity_checked':True,
          'photo_id':photo,'posted_ms':int(cand['created_ms']),
          'source_sha256':sha,'source_url':source,
          'source_duration_seconds':round(durations[0],3),
          'public_duration_seconds':round(durations[1],3),
          'frame_inliers':scores,
          'public_url':'https://www.kwai.com/@'+ACCOUNT+'/video/'+photo}
   out=call('unproven',{'mode':'confirm','id':jid,'proof':proof})
   if out.get('ok'):
    print('KWAI_UNPROVEN_MEDIA_CONFIRMED',jid,proof['public_url'],flush=True);return
   print('KWAI_UNPROVEN_CONFIRM_CALLBACK_PENDING',jid,out.get('error',''),flush=True)
   return
  except Exception as e:
   print('KWAI_UNPROVEN_CANDIDATE_MEDIA_INCONCLUSIVE',jid,type(e).__name__,str(e)[:140],flush=True)
 if oldest>started_ms-18*60000 or newest<started_ms+18*60000:
  print('KWAI_UNPROVEN_PUBLIC_WINDOW_INCOMPLETE',jid,flush=True)
  return
 proof={'kind':'kwai_bounded_public_scan_discard_v1','job_id':jid,
        'account':ACCOUNT,'authenticated_identity_checked':logged,
        'scanned_at_epoch_ms':int(time.time()*1000),'confirmed_public_media':False,
        'result':'candidate_unproven' if candidates else 'complete_absence',
        'attempt_count':1,'oldest_public_ms':int(oldest),
        'newest_public_ms':int(newest),'scanned_items':len(feed),
        'candidate_photo_ids':[x['photo_id'] for x in candidates][:15]}
 out=call('unproven',{'mode':'discard','id':jid,'proof':proof})
 print('KWAI_UNPROVEN_TERMINAL_DISCARD',jid,out.get('ok'),out.get('error',''),flush=True)

def main():
 from cortes_neon_queue_client import call
 try:
  response=call('unproven',{'mode':'list'})
  if not response.get('ok'):raise RuntimeError(str(response.get('error','UNPROVEN_LIST_FAILED')))
  jobs=response.get('jobs') or []
  if not jobs:
   print('KWAI_UNPROVEN_NOTHING_TO_RECONCILE',flush=True);return 0
  for item in jobs[:4]:
   try:check(item)
   except Exception as exc:
    print('KWAI_UNPROVEN_JOB_RECONCILE_ERROR',item.get('id'),type(exc).__name__,str(exc)[:140],flush=True)
  return 0
 finally:
  try:adb('shell','rm','-f',TEMP,timeout=8,check=False)
  except Exception:pass

if __name__=='__main__':sys.exit(main())
