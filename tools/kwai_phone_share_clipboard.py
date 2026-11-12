#!/usr/bin/env python3
"""Extract verified posted Kwai Lite short link using the existing phone HID and Chrome."""
from __future__ import annotations
import html,json,os,pathlib,re,subprocess,sys,time,unicodedata,urllib.parse,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[1]
STATE=ROOT/'.state'/'kwai-native-cortes'
ADB=os.getenv('ANTHARES_ADB',r'C:\Users\Lucas\.kwai-up\platform-tools\adb.exe')
PORT=os.getenv('ANTHARES_PHYSICAL_ADB_PORT','5038')
SERIAL=os.getenv('ANTHARES_PHYSICAL_ADB_SERIAL','993fce720408')
TOUCH='/data/local/tmp/anthares-hid-tap.sh'
PASTE='/data/local/tmp/anthares-keyboard-paste.sh'
VID=re.compile(r'https://(?:kwai-video\.com|k\.kwai\.com)/p/([A-Za-z0-9_-]{5,100})')
ACCOUNT=os.getenv('KWAI_EXPECTED_ACCOUNT','lucasrosalem').strip().lstrip('@').lower()
if ACCOUNT not in ('lucasrosalem','universoanthares'):raise RuntimeError('KWAI_SHARE_ACCOUNT_INVALID')
APP='com.kwai.video' if ACCOUNT=='universoanthares' else 'kwai.lite.video'
DETAIL=APP+'/com.yxcorp.gifshow.detail.PhotoDetailNewActivity'
AUTHOR='Universo Anthares' if ACCOUNT=='universoanthares' else 'Lucas Rosalem'

def adb(*args,timeout=45,check=True):
    p=subprocess.run([ADB,'-P',PORT,'-s',SERIAL,*args],capture_output=True,timeout=timeout)
    if check and p.returncode:
        raise RuntimeError('KWAI_ADB_FAILURE:'+str(p.returncode))
    return p.stdout.decode('utf8','replace')

def nodes(label):
    dest='/data/local/tmp/kwai-'+label+'.xml'
    adb('shell','uiautomator','dump',dest,timeout=43,check=False)
    root=ET.fromstring(adb('exec-out','cat',dest,timeout=20))
    return list(root.iter('node'))

def norm(s):
    s=unicodedata.normalize('NFKD',html.unescape(s))
    return ''.join(c for c in s if not unicodedata.combining(c)).casefold()

def one(items,rid):
    matches=[n for n in items if n.attrib.get('resource-id')==rid]
    if len(matches)!=1:raise RuntimeError('KWAI_SHARE_UI_MISSING:'+rid)
    return matches[0]

def point(item):
    m=re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',item.attrib.get('bounds',''))
    if not m:raise RuntimeError('KWAI_INVALID_BOUNDS')
    a,b,c,d=map(int,m.groups())
    return (a+c)//2,(b+d)//2

def tap(x,y):
    adb('shell',TOUCH,str(x),str(y),timeout=21)

def capture(jobid):
    path=STATE/(jobid+'.json')
    st=json.loads(path.read_text(encoding='utf8'))
    if (st.get('job_id')!=jobid or st.get('state')!='verified' or
        st.get('publication_attempted') is not True or
        st.get('expected_account')!=ACCOUNT):
        raise RuntimeError('KWAI_VERIFIED_NATIVE_STATE_REQUIRED')
    focused=adb('shell','dumpsys','window')
    if DETAIL not in focused:raise RuntimeError('KWAI_NATIVE_POST_DETAIL_NOT_ACTIVE')
    current=nodes('share-proof-target')
    author=one(current,APP+'.basis:id/tv_slide_play_user_name').attrib.get('text','')
    if author!=AUTHOR:raise RuntimeError('KWAI_POST_AUTHOR_UI_MISMATCH')
    # Kwai removes the description widget for real captionless posts. A
    # missing caption node is legitimate only for the native verified
    # caption_optional=True and exact empty caption contract.
    caption_nodes=[n for n in current if n.attrib.get('resource-id')==
                   APP+'.basis:id/slide_play_tv_user_info_desc']
    if st.get('caption_optional') is True and st.get('caption')=='':
        if len(caption_nodes)>1:
            raise RuntimeError('KWAI_CAPTIONLESS_DESCRIPTION_AMBIGUOUS')
        if caption_nodes and norm(caption_nodes[0].attrib.get('text','')) not in ('','mais'):
            raise RuntimeError('KWAI_CAPTIONLESS_PUBLIC_DESCRIPTION_NOT_EMPTY')
    else:
        if len(caption_nodes)!=1:
            raise RuntimeError('KWAI_CAPTION_REQUIRED_DESCRIPTION_MISSING')
        if norm(st['caption'])[:25]!=norm(caption_nodes[0].attrib.get('text',''))[:25]:
            raise RuntimeError('KWAI_POST_CAPTION_UI_MISMATCH')

    post_time=one(current,APP+'.basis:id/tv_slide_play_post_time').attrib.get('text','')
    if not re.search(r'\d{4}-\d\d-\d\d',post_time):
        raise RuntimeError('KWAI_POST_TIME_UI_MISSING')
    exact=(st.get('profile_verification') or {}).get('post_time')
    if exact and exact!=post_time:
        raise RuntimeError('KWAI_POST_TIME_CHANGED_BEFORE_SHARE')
    tap(*point(one(current,APP+'.basis:id/forward_button')))
    time.sleep(.5)
    sheet=nodes('share-proof-sheet')
    label=next((n for n in sheet if n.attrib.get('text')=='Copiar link' and
                n.attrib.get('resource-id')==APP+'.basis:id/share_to_text'),None)
    if label is None:raise RuntimeError('KWAI_POST_COPY_LINK_BUTTON_MISSING')
    x,y=point(label)
    copy_started_at=int(time.time()*1000)
    tap(x,y-100)
    adb('shell','am','start','-W','-a','android.intent.action.VIEW',
        '-d','https://example.com','-p','com.android.chrome',timeout=30)
    value=''
    for k in range(5):
        tap(415,154)
        time.sleep(.35)
        chrome=nodes('share-proof-chrome-focused')
        field=next((n for n in chrome if n.attrib.get('resource-id')=='com.android.chrome:id/url_bar'),None)
        if field is None or field.attrib.get('focused')!='true':continue
        adb('shell','sh',PASTE,timeout=15)
        time.sleep(.2)
        chrome=nodes('share-proof-chrome-readback')
        field=next((n for n in chrome if n.attrib.get('resource-id')=='com.android.chrome:id/url_bar'),None)
        value=(field.attrib.get('text') or '') if field is not None else ''
        if VID.search(value):break
        time.sleep(.4)
    match=VID.search(value)
    if not match:raise RuntimeError('KWAI_COPIED_SHARE_URL_NOT_VISIBLE')
    short='https://k.kwai.com/p/'+match.group(1)
    curl=subprocess.run(['curl.exe','-LsS','--max-time','25','--max-redirs','5',
         '-o','NUL','-w','%{url_effective}',short],capture_output=True,text=True,timeout=30)
    if curl.returncode:raise RuntimeError('KWAI_SHARE_REDIRECT_UNAVAILABLE')
    u=urllib.parse.urlsplit(curl.stdout.strip())
    mm=re.fullmatch(r'/@'+re.escape(ACCOUNT)+r'/video/([0-9]{16,21})',u.path)
    params=urllib.parse.parse_qs(u.query)
    if (u.scheme!='https' or u.hostname!='www.kwai.com' or
        not mm or params.get('photoId')!=[mm.group(1)] or
        params.get('authorKwaiId')!=[ACCOUNT]):
        raise RuntimeError('KWAI_OFFICIAL_SHARE_AUTHOR_ID_INVALID')
    receipt=int(params.get('timestamp',['0'])[0])
    now=int(time.time()*1000)
    if not (st['publication_attempted_at']*1000-600000 <=receipt<=now+10000 and
            copy_started_at-5000<=receipt):
        raise RuntimeError('KWAI_SHARE_RECEIPT_OUTSIDE_PUBLICATION')
    st['verified_short_url']=short
    st['share_receipt_epoch_ms']=receipt
    st['official_permalink_candidate']='https://www.kwai.com'+u.path
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(st,ensure_ascii=False,indent=2),encoding='utf8')
    tmp.replace(path)
    print('KWAI_SHARE_CLIPBOARD_RECEIPT=PASS job='+jobid+' short='+short+
          ' official='+st['official_permalink_candidate']+
          ' author='+ACCOUNT)
    return 0
if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('usage: kwai_phone_share_clipboard.py JOB_ID')
    try:raise SystemExit(capture(sys.argv[1]))
    except Exception as exc:
        print('KWAI_PHYSICAL_COPY_LINK_PENDING '+type(exc).__name__+':'+str(exc)[:200],flush=True)
        raise SystemExit(75)
