#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,os,pathlib,re,subprocess,sys,time,xml.etree.ElementTree as ET
from datetime import datetime,timedelta
from android_adb_inventory import online_devices

ROOT=pathlib.Path(__file__).resolve().parents[1]
STATE=ROOT/'.state'/'kwai-native-cortes'; EVID=ROOT/'.state'/'kwai-native-evidence'
ADB=os.getenv('ANTHARES_ADB',r'C:\Users\Lucas\.kwai-up\platform-tools\adb.exe')
SERIAL_HINT=os.getenv('ANTHARES_PHYSICAL_ADB_SERIAL','').strip(); MODEL='M2004J19C'
PKG=os.getenv('KWAI_UP_PACKAGE','kwai.lite.video'); JOB=os.getenv('KWAI_UP_JOB_ID','').strip()
MEDIA=pathlib.Path(os.getenv('KWAI_UP_MEDIA','')) if os.getenv('KWAI_UP_MEDIA') else None
EXPECTED_SHA=os.getenv('KWAI_MEDIA_SHA256','').strip().lower()
ACCOUNT=os.getenv('KWAI_UP_EXPECTED_ACCOUNT',os.getenv('KWAI_EXPECTED_ACCOUNT','lucasrosalem')).strip().lstrip('@').lower()
CAPTION_OPTIONAL=os.getenv('ANTHARES_KWAI_CAPTION_OPTIONAL','0')=='1'
CAPTION='' if CAPTION_OPTIONAL else os.getenv('KWAI_UP_CAPTION',os.getenv('KWAI_VIDEO_TITLE','')).strip()
TOUCH='/data/local/tmp/anthares-hid-tap.sh'; NATIVE='/data/local/tmp/anthares-kwai-native.sh'
MEDIA_URI='content://media/external/video/media'; REMOTE_DIR='/sdcard/DCIM/Anthares'
RID_PROFILE='com.kwai.video.basis:id/id_home_bottom_tab_me'; RID_USER='com.kwai.video.basis_extension:id/tv_user_id'
RID_THUMB='com.kwai.video.basis_extension:id/thumb'; RID_NEXT='com.kwai.video.product:id/edit_post_next_step_button'
RID_EDITOR='kwai.lite.video.basis:id/editor'; RID_POST='kwai.lite.video.basis:id/post'; RID_PUBLIC='kwai.lite.video.ca_product:id/tv_select_permission'
RID_NAME='com.kwai.video.basis:id/tv_slide_play_user_name'; RID_CAP='com.kwai.video.basis:id/slide_play_tv_user_info_desc'; RID_TIME='com.kwai.video.basis:id/tv_slide_play_post_time'

class E(RuntimeError): pass

def out(s): print(s,flush=True)
def safe(): return re.sub(r'[^A-Za-z0-9._-]+','_',JOB)[-100:]
def spath(): return STATE/(safe()+'.json')
def load():
 try:
  d=json.loads(spath().read_text(encoding='utf-8')); return d if isinstance(d,dict) else {}
 except (OSError,json.JSONDecodeError): return {}
def save(d):
 STATE.mkdir(parents=True,exist_ok=True); p=spath(); t=p.with_suffix('.tmp'); t.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True),encoding='utf-8'); t.replace(p)
def run(a,timeout=60,check=True,text=True):
 p=subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout,check=False,text=text)
 if check and p.returncode: raise E(f'cmd-failed:{p.returncode}:{str(p.stderr)[-500:]}')
 return p
def acmd(serial,*a): return [ADB,'-P',os.getenv('ANTHARES_PHYSICAL_ADB_PORT','5037')]+(['-s',serial] if serial else [])+list(a)
def adb(serial,*a,timeout=60,check=True,text=True): return run(acmd(serial,*a),timeout,check,text)
def devices():
 p=adb(None,'devices','-l',check=False)
 return online_devices(p.stdout or '') if p.returncode==0 else []
def connect():
 for d in devices():
  if d.get('model')==MODEL or (SERIAL_HINT and d['serial']==SERIAL_HINT): return verify_device(d['serial'])
 if SERIAL_HINT: adb(None,'connect',SERIAL_HINT,check=False,timeout=20)
 p=adb(None,'mdns','services',check=False,timeout=20)
 for ep in re.findall(r'(\d{1,3}(?:\.\d{1,3}){3}:\d+)',p.stdout or ''): adb(None,'connect',ep,check=False,timeout=20)
 for d in devices():
  if d.get('model')==MODEL or (SERIAL_HINT and d['serial']==SERIAL_HINT): return verify_device(d['serial'])
 raise E('physical-device-unavailable')
def verify_device(s):
 if adb(s,'get-state').stdout.strip()!='device': raise E('device-not-ready')
 if adb(s,'shell','getprop','ro.product.model').stdout.strip()!=MODEL: raise E('wrong-model')
 if 'package:' not in adb(s,'shell','pm','path',PKG,check=False).stdout: raise E('kwai-missing')
 if '1080x2340' not in adb(s,'shell','wm','size').stdout: raise E('wrong-screen')
 if adb(s,'shell','test','-x',NATIVE,check=False).returncode: raise E('native-executor-missing')
 if adb(s,'shell','test','-x',TOUCH,check=False).returncode: raise E('hid-touch-helper-missing')
 return s
def dump(s,name):
 EVID.mkdir(parents=True,exist_ok=True); remote=f'/data/local/tmp/{name}.xml'; local=EVID/(name+'.xml')
 for attempt in range(3):
  local.unlink(missing_ok=True)
  adb(s,'shell','rm','-f',remote,timeout=10,check=False)
  d=adb(s,'shell','uiautomator','dump',remote,timeout=35,check=False)
  if d.returncode==0:
   p=adb(s,'pull',remote,str(local),timeout=30,check=False)
   if p.returncode==0 and local.is_file():
    try: return ET.fromstring(local.read_bytes()),local
    except ET.ParseError: pass
  time.sleep(1)
 raise E('ui-dump-unavailable:'+name)
def rid(root,r):
 # Exact whitelisted UI variants; package installation name differs from view ids.
 known={
  RID_PROFILE:('kwai.lite.video.basis:id/id_home_bottom_tab_me',),
  RID_NEXT:('kwai.lite.video.product:id/edit_post_next_step_button','kwai.lite.video.ca_product:id/next_button_normal','com.kwai.video.ca_product:id/next_button_normal'),
  RID_EDITOR:('com.kwai.video.basis:id/editor',),
  RID_POST:('com.kwai.video.basis:id/post','com.kwai.video.basis:id/right_btn'),
  RID_PUBLIC:('com.kwai.video.ca_product:id/tv_select_permission',),
  RID_USER:('kwai.lite.video.basis:id/tv_user_id','kwai.lite.video.basis_extension:id/tv_user_id','com.kwai.video.basis:id/tv_user_id'),
  RID_THUMB:('kwai.lite.video.basis:id/thumb','kwai.lite.video.basis_extension:id/thumb','com.kwai.video.basis:id/thumb'),
  RID_NAME:('kwai.lite.video.basis:id/tv_slide_play_user_name',),
  RID_CAP:('kwai.lite.video.basis:id/slide_play_tv_user_info_desc',),
  RID_TIME:('kwai.lite.video.basis:id/tv_slide_play_post_time',),
 }
 variants=(r,)+known.get(r,())
 return [n for n in root.iter('node') if n.attrib.get('resource-id') in variants]
def center(b):
 m=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',b or '')
 if not m:return None
 x1,y1,x2,y2=map(int,m.groups()); return ((x1+x2)//2,(y1+y2)//2) if x2>x1 and y2>y1 else None
def tap(s,n):
 p=center(n.attrib.get('bounds',''))
 if not p: raise E('bad-bounds')
 adb(s,'shell',TOUCH,str(p[0]),str(p[1]),timeout=15); return p
def wait(s,r,name,seconds=30):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  root,path=dump(s,name); xs=rid(root,r)
  if xs and r==RID_PROFILE:
   xs=[n for n in xs if n.attrib.get("clickable")=="true" and n.attrib.get("enabled")=="true" and center(n.attrib.get("bounds",""))]
   xs.sort(key=lambda n:center(n.attrib["bounds"])[0],reverse=True)
  if xs:return root,xs[0],path
  # Both Kwai variants can display an optional notifications promotion over
  # the authenticated profile tab. Dismiss only its exact close control, never
  # the permission/enable button; preserve account and privacy settings.
  prefix='com.kwai.video' if ACCOUNT=='universoanthares' else 'kwai.lite.video'
  # Secondary Kwai may present the same optional promotional popup already
  # handled in kwai_up.py. Match all three exact controls before closing it.
  # Unknown prompts, login and security dialogs remain untouched.
  if r==RID_PROFILE and ACCOUNT=='universoanthares':
   promo_ids={n.attrib.get('resource-id','') for n in root.iter('node')}
   promo_required={'com.kwai.video.basis:id/view_content',
                   'com.kwai.video:id/colored_button_bg',
                   'com.kwai.video:id/close_button'}
   if promo_required.issubset(promo_ids):
    promo_close=[n for n in root.iter('node')
      if n.attrib.get('resource-id')=='com.kwai.video:id/close_button'
      and n.attrib.get('clickable')=='true'
      and n.attrib.get('enabled')=='true'
      and center(n.attrib.get('bounds',''))]
    if len(promo_close)==1:
     tap(s,promo_close[0]);time.sleep(1);continue
  notification_prompt=any(
   n.attrib.get('resource-id')==prefix+'.basis:id/tv_dialog_title' and
   'notifica' in (n.attrib.get('text') or '').casefold()
   for n in root.iter('node'))
  notification_close=[n for n in root.iter('node')
   if n.attrib.get('resource-id')==prefix+':id/iv_close'
   and n.attrib.get('clickable')=='true'
   and n.attrib.get('enabled')=='true'
   and center(n.attrib.get('bounds',''))]
  if r==RID_PROFILE and notification_prompt and len(notification_close)==1:
   tap(s,notification_close[0]);time.sleep(1);continue
  # Redmi 9 can open Android's USB-use chooser while the cable is
  # connected. Cancel this system overlay to preserve the existing USB mode.
  usb_alert=any(n.attrib.get('resource-id')=='com.android.settings:id/alertTitle'
    and (n.attrib.get('text') or '').strip()=='Usar USB para'
    for n in root.iter('node'))
  usb_cancel=[n for n in root.iter('node')
    if n.attrib.get('resource-id')=='android:id/button2' and
    (n.attrib.get('text') or '').strip()=='Cancelar']
  if usb_alert and len(usb_cancel)==1:
   tap(s,usb_cancel[0]);time.sleep(1);continue
  # Dismiss only the known, optional birthdate promotion.
  notice=any('data de nascimento' in (n.attrib.get('text') or '').lower()
             for n in root.iter('node'))
  dismiss=[n for n in root.iter('node') if
           n.attrib.get('resource-id')=='kwai.lite.video.basis:id/second_button' and
           (n.attrib.get('text') or '').strip().lower().startswith('agora')]
  if notice and len(dismiss)==1:
   tap(s,dismiss[0]); time.sleep(1); continue
  # Close the optional Kwai creator-family popup without joining anything.
  creator_close=[n for n in root.iter('node') if
    n.attrib.get('resource-id')=='kwai.lite.video.basis_extension:id/fmy_guide_close']
  if r==RID_USER and len(creator_close)==1 and any(
    n.attrib.get('resource-id')=='kwai.lite.video.basis_extension:id/fmy_guide_banner_viewpager'
    for n in root.iter('node')):
   tap(s,creator_close[0]);time.sleep(1);continue
  # Known Kwai Lite overlay-permission promotion on the published-video
  # details page. Close the optional notice; never enable permissions.
  overlay_close=[n for n in root.iter('node') if
     n.attrib.get('resource-id')=='kwai.lite.video:id/iv_close']
  if r==RID_NAME and len(overlay_close)==1 and any(
      n.attrib.get('resource-id')=='kwai.lite.video.basis:id/after_popups_frame'
      for n in root.iter('node')) and any(
      n.attrib.get('resource-id')=='kwai.lite.video.basis:id/lottie_overlay_guide'
      for n in root.iter('node')):
   tap(s,overlay_close[0]);time.sleep(1);continue
  # Profile can be scrolled down after a prior operation, hiding the Kwai ID.
  # Restore it with the existing authenticated HID touch interface before
  # resolving identity; never substitute the display name for the exact ID.
  if r==RID_USER and (
      (ACCOUNT=='lucasrosalem' and any(
          n.attrib.get('resource-id')=='kwai.lite.video.basis_extension:id/profile_root'
          for n in root.iter('node')) and any(
          n.attrib.get('resource-id')=='kwai.lite.video.basis:id/title_tv' and
          (n.attrib.get('text') or '').strip()=='Lucas Rosalem'
          for n in root.iter('node')))
      or (ACCOUNT=='universoanthares' and any(
          n.attrib.get('resource-id')=='com.kwai.video.basis:id/title_tv' and
          (n.attrib.get('text') or '').strip()=='Universo Anthares'
          for n in root.iter('node')) and any(
          n.attrib.get('resource-id')=='com.kwai.video.basis_extension:id/profile_settings_button' and
          (n.attrib.get('text') or '').strip()=='Editar perfil'
          for n in root.iter('node')))):
   # Recover hidden @handle on the logged-in profile; exact ID remains required.
   adb(s,'shell','sh','/data/local/tmp/anthares-kwai-profile-scroll.sh',timeout=16)
   time.sleep(1);continue
  if r==RID_PROFILE and any(n.attrib.get('resource-id','').endswith(('/edit_post_next_step_button','/post_button_normal')) for n in root.iter('node')):
   raise E('ui-surface-unexpected:editor-screen-active:preserve-draft')
  time.sleep(1)
 raise E('missing:'+r)
def shot(s,name):
 EVID.mkdir(parents=True,exist_ok=True); p=run(acmd(s,'exec-out','screencap','-p'),25,True,False); f=EVID/(name+'.png'); f.write_bytes(p.stdout); return f
def home(s,preserve_upload=False):
 # Validated on Kwai Lite 2026-10-22. Explicit HomeActivity retains the upload
 # task, unlike am force-stop or a launcher intent that resumes EditorActivity.
 out('KWAI_NATIVE_PRESERVE_UPLOAD=1')
 if "mWakefulness=Asleep" in (adb(s,"shell","dumpsys","power",timeout=15).stdout or ""):
  adb(s,"shell",TOUCH,"540","1200",timeout=15)
  time.sleep(1)
 activity=PKG+'/com.yxcorp.gifshow.homepage.HomeActivity'
 # Preserve an existing editor while bringing the HomeActivity to the foreground.
 p=adb(s,'shell','am','start','--activity-reorder-to-front','-n',activity,check=False,timeout=25)
 if p.returncode or 'Error' in (p.stdout or ''):
  out('KWAI_NATIVE_HOME_INTENT_UNAVAILABLE')
  adb(s,'shell','monkey','-p',PKG,'-c','android.intent.category.LAUNCHER','1',check=False,timeout=25)
 time.sleep(3)
def latest(s,prefix,preserve_upload=False):
 home(s,preserve_upload=preserve_upload)
 for attempt in range(2):
  _,tab,_=wait(s,RID_PROFILE,prefix+'-home-'+str(attempt),25)
  tap(s,tab); time.sleep(4)
  try:
   root,user,px=wait(s,RID_USER,prefix+'-profile-'+str(attempt),12 if attempt==0 else 30)
   break
  except E as exc:
   if attempt or not str(exc).startswith('missing:'+RID_USER): raise
 account=(user.attrib.get('text') or '').strip().lstrip('@').lower()
 if account!=ACCOUNT: raise E('profile-account:'+account)
 thumbs=[n for n in rid(root,RID_THUMB) if n.attrib.get('clickable')=='true' and center(n.attrib.get('bounds',''))]
 if not thumbs:
  if ACCOUNT!='universoanthares':raise E('no-published-thumb')
  # A new secondary account may have no prior public video. The account ID
  # was verified above; final confirmation still requires the exact new post.
  return {'account':account,'display_name':'','caption':'','post_time':'',
          'profile_xml':str(px),'detail_xml':'','screenshot':str(shot(s,prefix+'-empty-profile')),
          'profile_empty':True}
 thumbs.sort(key=lambda n:(center(n.attrib['bounds'])[1],center(n.attrib['bounds'])[0])); tap(s,thumbs[0]); time.sleep(4)
 detail,_,dx=wait(s,RID_NAME,prefix+'-detail',30)
 def text(r):
  xs=rid(detail,r); return (xs[0].attrib.get('text') or '').strip() if xs else ''
 return {'account':account,'display_name':text(RID_NAME),'caption':text(RID_CAP),'post_time':text(RID_TIME),'profile_xml':str(px),'detail_xml':str(dx),'screenshot':str(shot(s,prefix+'-detail'))}
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def media():
 if MEDIA is None or not MEDIA.is_file() or MEDIA.stat().st_size<1024: raise E('media-missing')
 digest=sha(MEDIA)
 if EXPECTED_SHA and digest!=EXPECTED_SHA: raise E('media-sha-mismatch')
 return MEDIA,digest
def stage(s,path,digest):
 # Resilient content-addressed staging. Reuse a phone file only after exact
 # SHA-256 proof; this avoids repeated 6MB ADB pushes and blocking scanner
 # broadcasts when an earlier PRE-COMMIT prepare failed.
 name=f'anthares-{safe()[-70:]}-{digest[:12]}.mp4'
 remote=f'{REMOTE_DIR}/{name}'
 adb(s,'shell','mkdir','-p',REMOTE_DIR,timeout=12)
 known=adb(s,'shell','sha256sum',remote,timeout=12,check=False)
 if known.returncode==0:
  value=(known.stdout or '').split()
  if not value or value[0].lower()!=digest.lower():
   raise E('kwai_phone_media_same_name_different_sha256')
  out('KWAI_PHONE_MEDIA_REUSED_VERIFIED_SHA256=1')
 else:
  out('KWAI_PHONE_MEDIA_STAGE_PUSH_REQUIRED=1')
  adb(s,'push',str(path),remote,timeout=120)
  delivered=adb(s,'shell','sha256sum',remote,timeout=12,check=False)
  actual=(delivered.stdout or '').split()
  if delivered.returncode or not actual or actual[0].lower()!=digest.lower():
   raise E('kwai_phone_media_push_sha256_mismatch')
  out('KWAI_PHONE_MEDIA_PUSH_VERIFIED_SHA256=1')
 def unique_media_row():
  try:
   p=adb(s,'shell','content','query','--uri',MEDIA_URI,
         '--projection','_id:_display_name:_data:duration:width:height',
         timeout=12,check=False)
  except subprocess.TimeoutExpired:
   out('KWAI_MEDIASTORE_QUERY_TIMEOUT_PRECOMMIT=1')
   return None
  if p.returncode:
   out('KWAI_MEDIASTORE_QUERY_FAILED_PRECOMMIT=1')
   return None
  rows=[line for line in (p.stdout or '').splitlines()
        if '_display_name='+name in line]
  if len(rows)>1:raise E('kwai_mediastore_ambiguous_duplicate')
  if not rows:return None
  match=re.search(r'(?:^|[,\s])_id=(\d+)',rows[0])
  if not match:raise E('kwai_mediastore_id_missing')
  return match.group(1)
 media_id=unique_media_row()
 if not media_id:
  # Fire the scanner only when MediaStore does not already contain this media.
  # A stalled asynchronous Android broadcast must never consume the entire
  # preparation budget or trigger a speculative publication.
  try:
   adb(s,'shell','am','broadcast','-a','android.intent.action.MEDIA_SCANNER_SCAN_FILE',
       '-d','file://'+remote,timeout=10,check=False)
  except subprocess.TimeoutExpired:
   out('KWAI_MEDIA_SCAN_BROADCAST_TIMEOUT_PRECOMMIT=1')
  for _ in range(5):
   time.sleep(1)
   media_id=unique_media_row()
   if media_id:break
 if not media_id:raise E('kwai_mediastore_index_unavailable_precommit')
 out('KWAI_MEDIASTORE_UNIQUE_MEDIA_ID_VERIFIED=1')
 return remote,MEDIA_URI+'/'+media_id

def publish_ui(s,name):
 root,path=dump(s,name)
 editors=rid(root,RID_EDITOR); posts=rid(root,RID_POST); permissions=rid(root,RID_PUBLIC)
 # Current ShareActivity publishes through right_btn=Publicar; bind the
 # fallback to this exact account-specific text and enabled control.
 posts=[n for n in posts if n.attrib.get("resource-id")!=
        "com.kwai.video.basis:id/right_btn" or (
        (n.attrib.get("text") or "").strip().casefold()=="publicar"
        and n.attrib.get("clickable")=="true")]
 if len(editors)!=1 or len(posts)!=1 or len(permissions)!=1:
  raise E('kwai-publish-ui-contract-mismatch')
 if posts[0].attrib.get('enabled')!='true':
  raise E('kwai-publish-disabled')
 if (permissions[0].attrib.get('text') or '').strip()!='Público':
  raise E('kwai-public-privacy-required')
 current_caption=(editors[0].attrib.get('text') or '').strip()
 hint=bool(re.fullmatch(
  r'Descreva sua publica.{1,3}o, adicione hashtags ou @amigos',
  current_caption,flags=re.IGNORECASE)) and editors[0].attrib.get('class')=='android.widget.EditText'
 if current_caption!=CAPTION and not (CAPTION_OPTIONAL and CAPTION=='' and hint):
  raise E('kwai-caption-differs-from-target')
 return root

def editor(s,uri):
 # Android am start -W can hang until full editor initialization even when
 # intent delivery succeeded. Launch asynchronously, then verify exact UI
 # nodes before proceeding. No Publish action occurs during prepare.
 adb(s,'shell','am','start','-a','android.intent.action.SEND',
     '-t','video/mp4','--eu','android.intent.extra.STREAM',uri,'-p',PKG,timeout=15)
 _,n,_=wait(s,RID_NEXT,safe()+'-editor',35)
 if n.attrib.get('enabled')!='true': raise E('next-disabled')
 tap(s,n)
 try:
  wait(s,RID_EDITOR,safe()+'-publish-form',12)
 except E as err:
  if str(err)!='missing:'+RID_EDITOR:
   raise
  # The editor's first Next tap may be absorbed during video preview
  # initialization. Retry only while the same enabled Next control remains
  # visible; never touch the nearby direct-Publish control.
  _,retry,_=wait(s,RID_NEXT,safe()+'-editor-next-retry',12)
  if retry.attrib.get('enabled')!='true':raise E('next-retry-disabled')
  tap(s,retry)
  wait(s,RID_EDITOR,safe()+'-publish-form-retry',22)
 env=os.environ.copy()
 env['ANTHARES_PHYSICAL_ADB_SERIAL']=s
 env['ANTHARES_ADB']=ADB
 if CAPTION_OPTIONAL:
  root,_,_=wait(s,RID_EDITOR,safe()+'-caption-optional-check',15)
  fields=rid(root,RID_EDITOR)
  # Kwai exposes its native EditText hint through UIAutomator as `text`,
  # even when the actual caption is empty. Accept only the exact documented
  # placeholder on the authenticated ShareActivity (never arbitrary text).
  if len(fields)!=1:
   raise E('kwai_caption_optional_editor_missing_or_ambiguous')
  content=(fields[0].attrib.get('text') or '').strip()
  placeholder=bool(re.fullmatch(
   r'Descreva sua publica.{1,3}o, adicione hashtags ou @amigos',content,
   flags=re.IGNORECASE)) and fields[0].attrib.get('class')=='android.widget.EditText'
  if content and not placeholder:
   raise E('kwai_caption_optional_stale_editor_text')
  out('KWAI_CAPTION_OPTIONAL_BLANK_EDITOR_VERIFIED')
  return
 proc=subprocess.run([sys.executable,str(ROOT/'tools'/'kwai_hid_caption.py'),CAPTION],
       capture_output=True,text=True,timeout=145,env=env)
 if proc.returncode or 'KWAI_CAPTION_READBACK=PASS' not in (proc.stdout or ''):
  raise E('kwai-caption-auto-fill-failed:'+str((proc.stderr or proc.stdout or '')[-240:]))
 out('KWAI_CAPTION_AUTOMATED=PASS')

def ptime(t):
 for f in ('%Y-%m-%d %I:%M %p','%Y-%m-%d %H:%M','%d/%m/%Y %H:%M','%d/%m/%Y %I:%M %p'):
  try:return datetime.strptime((t or '').strip(),f)
  except ValueError:pass
 return None
def confirm(s,baseline,tries=5,delay=15,attempted_at=0,expected_caption=None):
 time.sleep(25) # Allow async upload to progress before visiting profile
 last={}
 for i in range(tries):
  try:
   last=latest(s,f'{safe()}-verify-{i:02d}',preserve_upload=True); changed=(last.get('caption'),last.get('post_time'))!=(baseline.get('caption'),baseline.get('post_time'))
   dt=ptime(last.get('post_time',''))
   anchor=datetime.fromtimestamp(int(attempted_at)) if attempted_at else datetime.now()
   fresh=bool(dt and anchor-timedelta(minutes=5)<=dt<=anchor+timedelta(minutes=20))
   caption=expected_caption if expected_caption is not None else CAPTION
   title=bool(caption and caption.casefold() in (last.get('caption') or '').casefold())
   partial=bool(caption and caption[:28].casefold() in (last.get('caption') or '').casefold())
   if last.get('account')==ACCOUNT and changed and fresh and CAPTION_OPTIONAL and not caption:
    return True,last,'profile-account-post-time-caption-optional-await-media'
   if last.get('account')==ACCOUNT and changed and (title or (fresh and partial)): return True,last,'profile-account-title-time' if title else 'profile-account-post-time-and-caption-prefix'
  except E as e:last={'error':str(e)}
  if i+1<tries:time.sleep(delay)
 return False,last,''
def prepare():
 if not JOB or not re.fullmatch(r'[A-Za-z0-9._:-]{3,160}',JOB): raise E('bad-job-id')
 st=load()
 prior_attempt=bool(st.get('publication_attempted') or st.get('state') in ('publication_attempted','verified','uncertain'))
 historical=None
 if prior_attempt:
  # Only a new canonical Neon lease bearing independent public-absence proof
  # may supersede the prior, deliberately quarantined phone state.
  raw=os.getenv('KWAI_HISTORICAL_REQUEUE_PROOF_JSON','')
  try: historical=json.loads(raw)
  except (ValueError,TypeError): historical=None
  try:
   generation=int(os.getenv('KWAI_LEASE_GENERATION','0'))
   previous=int(historical['prior_lease_generation'])
   when=int(historical['previous_started_at_epoch_ms'])
  except (TypeError,KeyError,ValueError):
   generation=previous=when=0
  if (not isinstance(historical,dict) or
      historical.get('kind')!='kwai_historical_verified_public_absent_v1' or
      historical.get('job_id')!=JOB or historical.get('author_handle')!='lucasrosalem' or
      historical.get('attested_device')!='DESKTOP-FTDK0HP' or
      historical.get('device_signature_verified') is not True or
      not (0<previous<generation) or
      abs(when-int(st.get('publication_attempted_at') or 0)*1000)>5000 or
      historical.get('source_sha256')!=st.get('media_sha256') or
      int(historical.get('source_http_code') or 0)!=200):
   out('KWAI_UP_STATE=UNCERTAIN DEDUPE_GUARD=1 HISTORICAL_FENCE_REQUIRED=1')
   return 90
  out('KWAI_HISTORICAL_SAFE_REQUEUE=ACCEPTED CURRENT_LEASE='+str(generation))
 s=connect(); path,digest=media()
 if historical and digest!=historical['source_sha256']:
  raise E('historical-verified-source-sha256-changed')
 baseline=latest(s,safe()+'-baseline'); remote,uri=stage(s,path,digest); editor(s,uri)
 st={'job_id':JOB,'state':'ready','publication_attempted':False,'prepared_at':int(time.time()),'serial':s,'media_sha256':digest,'media_path':str(path),'remote_media':remote,'media_uri':uri,'expected_account':ACCOUNT,'caption':CAPTION,'caption_optional':CAPTION_OPTIONAL,'baseline':baseline}; save(st)
 out(f'KWAI_UP_STATE=READY_TO_PUBLISH SERIAL={s} SHA256={digest}'); return 0
def unlock_historical_android_attempt(s,st):
 # A signed Neon lease explicitly proved the October attempt absent from
 # the complete public feed. Preserve the Android's older attempt marker
 # before allowing the replacement publication. This never runs on ordinary
 # jobs, and never clears a marker created during the current lease.
 raw=os.getenv('KWAI_HISTORICAL_REQUEUE_PROOF_JSON','')
 if not raw:return
 try:
  p=json.loads(raw)
  generation=int(os.getenv('KWAI_LEASE_GENERATION','0'))
  prior=int(p['prior_lease_generation'])
  old=int(p['previous_started_at_epoch_ms'])
  proof_at=int(p['verified_at_epoch_ms'])
 except (ValueError,TypeError,KeyError) as ex:raise E('historical-native-proof-invalid') from ex
 if (p.get('kind')!='kwai_historical_verified_public_absent_v1' or
     p.get('job_id')!=JOB or p.get('author_handle')!='lucasrosalem' or
     p.get('attested_device')!='DESKTOP-FTDK0HP' or
     p.get('device_signature_verified') is not True or
     p.get('source_sha256')!=st.get('media_sha256') or
     p.get('source_http_code')!=200 or
     not(0<prior<generation) or
     old<1760000000000 or
     not (old<=proof_at<=int(time.time()*1000)+15000) or
     st.get('state')!='ready' or st.get('publication_attempted') or
     st.get('job_id')!=JOB):raise E('historical-native-lease-fence-invalid')
 base='/data/local/tmp/anthares-kwai-native/'+JOB
 mark=base+'.state'
 oldvalue=adb(s,'shell','cat',mark,check=False)
 if oldvalue.returncode:
  out('KWAI_HISTORICAL_NATIVE_MARKER_ABSENT CURRENT_LEASE='+str(generation))
  return
 if oldvalue.stdout.strip()!='PUBLICATION_ATTEMPTED_UNVERIFIED':
  raise E('historical-native-marker-unexpected')
 # Marker mtime must precede this verified public-absence scan.
 stamp=adb(s,'shell','stat','-c','%Y',mark,check=False)
 try:mtime=int(stamp.stdout.strip())
 except (ValueError,AttributeError):raise E('historical-native-marker-time-unreadable')
 if stamp.returncode or mtime*1000>proof_at+2000:
  raise E('historical-native-marker-newer-than-public-scan')
 archive=base+'.before-historical-requeue-lease-'+str(generation)+'.state'
 if adb(s,'shell','test','-e',archive,check=False).returncode==0:
  raise E('historical-native-marker-archive-collision')
 if adb(s,'shell','cat',mark,check=False).stdout.strip()!='PUBLICATION_ATTEMPTED_UNVERIFIED':
  raise E('historical-native-marker-changed-before-archive')
 mv=adb(s,'shell','mv',mark,archive,check=False)
 if mv.returncode or adb(s,'shell','test','-e',mark,check=False).returncode==0:
  raise E('historical-native-marker-archive-failed')
 out('KWAI_HISTORICAL_NATIVE_MARKER_ARCHIVED LEASE='+str(generation))

def commit():
 st=load()
 if not st or st.get('state')!='ready' or st.get('publication_attempted'): out('KWAI_UP_STATE=UNCERTAIN DEDUPE_GUARD=1'); return 90
 s=connect(); _,digest=media()
 if digest!=st.get('media_sha256'): raise E('media-changed-after-prepare')
 publish_ui(s,safe()+'commit-preflight')
 unlock_historical_android_attempt(s,st)
 st['publication_attempted']=True; st['state']='publication_attempted'; st['publication_attempted_at']=int(time.time()); save(st)
 p=adb(s,'shell',NATIVE,JOB,timeout=120,check=False); st['native_rc']=p.returncode; st['native_stdout']=(p.stdout or '')[-4000:]; st['native_stderr']=(p.stderr or '')[-2000:]; save(st)
 ok,proof,evidence=confirm(s,st.get('baseline') or {},attempted_at=st.get('publication_attempted_at',0),expected_caption=st.get('caption')); st['profile_verification']=proof; st['verification_evidence']=evidence
 if ok:
  st['state']='verified'; st['verified_at']=int(time.time()); save(st); out(f"KWAI_UP_STATE=VERIFIED EVIDENCE={evidence} POST_TIME={proof.get('post_time','')}"); return 0
 st['state']='uncertain'; st['uncertain_at']=int(time.time()); save(st); out('KWAI_UP_STATE=UNCERTAIN PROFILE_CONFIRMATION_MISSING'); return 90
def verify():
 st=load()
 if not st.get('publication_attempted'): raise E('publication-not-attempted')
 if st.get('state')=='verified': out('KWAI_UP_STATE=VERIFIED EVIDENCE='+st.get('verification_evidence','persisted')); return 0
 s=connect(); ok,proof,evidence=confirm(s,st.get('baseline') or {},6,10,attempted_at=st.get('publication_attempted_at',0),expected_caption=st.get('caption')); st['profile_verification']=proof; st['verification_evidence']=evidence
 if ok: st['state']='verified'; st['verified_at']=int(time.time()); save(st); out(f"KWAI_UP_STATE=VERIFIED EVIDENCE={evidence} POST_TIME={proof.get('post_time','')}"); return 0
 st['state']='uncertain'; save(st); out('KWAI_UP_STATE=UNCERTAIN PROFILE_CONFIRMATION_MISSING'); return 90
def main():
 if len(sys.argv)!=2 or sys.argv[1] not in ('prepare','commit','verify'): return 2
 try:return {'prepare':prepare,'commit':commit,'verify':verify}[sys.argv[1]]()
 except subprocess.TimeoutExpired as e:out('KWAI_UP_STATE=FAILED ERROR=timeout'); return 75
 except E as e:out('KWAI_UP_STATE=FAILED ERROR='+str(e)); return 79
 except Exception as e:out(f'KWAI_UP_STATE=FAILED ERROR={type(e).__name__}:{e}'); return 79
if __name__=='__main__': raise SystemExit(main())
