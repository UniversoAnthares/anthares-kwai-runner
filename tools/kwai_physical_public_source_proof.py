#!/usr/bin/env python3
"""Independent public Kwai profile+CDN readback for the existing physical Android publisher."""
from __future__ import annotations
import datetime, hashlib, html, json, os, pathlib, re, subprocess, sys, tempfile, time, urllib.parse
import cv2, numpy as np

ROOT=pathlib.Path(__file__).resolve().parents[1]
NATIVE=ROOT/'.state'/'kwai-native-cortes'
EVID=ROOT/'.state'/'kwai-memu-evidence'
ACCOUNT=os.getenv('KWAI_EXPECTED_ACCOUNT','lucasrosalem').strip().lstrip('@').lower()
if ACCOUNT not in ('lucasrosalem','universoanthares'):raise RuntimeError('KWAI_PROOF_ACCOUNT_INVALID')
PROFILE='https://www.kwai.com/@'+ACCOUNT
PLAYER='https://www.kwai.com/@'+ACCOUNT+'/video/'
IDPAT=re.compile(r'photo_id_str:"([0-9]{16,21})"')
PUBLIC_METHOD='public_profile_independent_cdn_video_frame_match'

def fetch(url, destination, seconds=32):
    u=urllib.parse.urlsplit(url)
    permitted={'www.kwai.com','aws-br-cdn.kwai.net','ak-br-cdn.kwai.net'}
    if u.scheme!='https' or u.hostname not in permitted:
        raise RuntimeError('KWAI_PUBLIC_HOST_NOT_ALLOWLISTED')
    cmd=['curl.exe','--fail','--location','--silent','--show-error',
         '--connect-timeout','9','--max-time',str(seconds),'--retry','1',
         '--output',str(destination),url]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=seconds+10)
    if p.returncode or not destination.is_file() or destination.stat().st_size<1000:
        raise RuntimeError('KWAI_PUBLIC_FETCH_FAILED:'+str(p.returncode))

def read_profile(path,native):
    body=path.read_text(encoding='utf-8')
    attempted=int(native['publication_attempted_at'])*1000
    candidates=[]
    for match in IDPAT.finditer(body):
        snippet=body[match.end():match.end()+3200]
        timestamp=re.search(r',timestamp:(\d{13})',snippet)
        if not timestamp:continue
        posted=int(timestamp.group(1))
        if abs(posted-attempted)<=10*60*1000:
            candidates.append((match.group(1),posted))
    unique=list(dict(candidates).items())
    if not unique:raise RuntimeError('KWAI_NO_RECENT_PUBLIC_PROFILE_POST')
    return unique

def attrs(body,prop):
    match=re.search(r'<meta[^>]*\b(?:property|name)="'+re.escape(prop)+r'"[^>]*\bcontent="([^"]*)"',body)
    return html.unescape(match.group(1)) if match else ''

def video_link(body):
    m=re.search(r'main_mv_urls:\[\{cdn:[^,]+,url:"([^"]+)"',body)
    if not m:raise RuntimeError('KWAI_NO_PUBLIC_CDN_VIDEO')
    url=json.loads('"'+m.group(1)+'"')
    if urllib.parse.urlsplit(url).hostname not in {'aws-br-cdn.kwai.net','ak-br-cdn.kwai.net'}:
        raise RuntimeError('KWAI_BAD_VIDEO_CDN')
    return url

def compare(source,remote):
    cap1=cv2.VideoCapture(str(source))
    cap2=cv2.VideoCapture(str(remote))
    try:
        frames1=int(cap1.get(cv2.CAP_PROP_FRAME_COUNT))
        frames2=int(cap2.get(cv2.CAP_PROP_FRAME_COUNT))
        w1=int(cap1.get(cv2.CAP_PROP_FRAME_WIDTH))
        h1=int(cap1.get(cv2.CAP_PROP_FRAME_HEIGHT))
        w2=int(cap2.get(cv2.CAP_PROP_FRAME_WIDTH))
        h2=int(cap2.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if min(frames1,frames2)<100 or abs(frames1-frames2)>4 or (w1,h1)!=(w2,h2):
            raise RuntimeError('KWAI_PUBLIC_MEDIA_DIMENSIONS_OR_DURATION_DIFFER')
        orb=cv2.ORB_create(nfeatures=950,fastThreshold=12)
        matcher=cv2.BFMatcher(cv2.NORM_HAMMING)
        results=[]
        for frame_id in [int((min(frames1,frames2)-1)*p) for p in (.07,.20,.34,.48,.62,.77,.91)]:
            cap1.set(cv2.CAP_PROP_POS_FRAMES,frame_id)
            cap2.set(cv2.CAP_PROP_POS_FRAMES,frame_id)
            ok1,im1=cap1.read();ok2,im2=cap2.read()
            if not ok1 or not ok2:raise RuntimeError('KWAI_MEDIA_FRAME_READ_FAILURE')
            gray1=cv2.cvtColor(im1,cv2.COLOR_BGR2GRAY)
            gray2=cv2.cvtColor(im2,cv2.COLOR_BGR2GRAY)
            kp1,d1=orb.detectAndCompute(gray1,None)
            kp2,d2=orb.detectAndCompute(gray2,None)
            count=0
            if d1 is not None and d2 is not None:
                candidates=matcher.knnMatch(d1,d2,k=2)
                hits=[pair[0] for pair in candidates if len(pair)==2 and pair[0].distance < .75*pair[1].distance]
                if len(hits)>=8:
                    pts1=np.float32([kp1[k.queryIdx].pt for k in hits]).reshape(-1,1,2)
                    pts2=np.float32([kp2[k.trainIdx].pt for k in hits]).reshape(-1,1,2)
                    matrix,mask=cv2.findHomography(pts1,pts2,cv2.RANSAC,5)
                    count=int(mask.sum()) if matrix is not None and mask is not None else 0
            mae=float(np.mean(cv2.absdiff(gray1,gray2)))
            results.append({'frame':frame_id,'inliers':count,'mae':round(mae,2)})
        if sum(1 for f in results if f['inliers']>=80 and f['mae']<12)<6:
            raise RuntimeError('KWAI_INDEPENDENT_VIDEO_SOURCE_MISMATCH')
        return {'inliers':sorted([f['inliers'] for f in results],reverse=True),
                'frames_compared':len(results),'frame_inliers_and_mae':results,
                'source_and_public_matching_frames':True}
    finally:
        cap1.release();cap2.release()

def recover(jobid,source_arg=None):
    if not re.fullmatch(r'[A-Za-z0-9._-]{12,160}',jobid):
        raise RuntimeError('KWAI_BAD_JOB_ID')
    statepath=NATIVE/(re.sub(r'[^A-Za-z0-9._-]+','_',jobid)[-100:]+'.json')
    native=json.loads(statepath.read_text(encoding='utf-8'))
    if native.get('job_id')!=jobid or native.get('expected_account')!=ACCOUNT or native.get('state')!='verified' or native.get('publication_attempted') is not True:
        raise RuntimeError('KWAI_PHYSICAL_PUBLICATION_NOT_VERIFIED')
    source=pathlib.Path(source_arg or native.get('media_path') or '__missing__')
    if not source.is_file() or source.stat().st_size<200000:
        # Public profile indexing may lag the real Kwai post; reacquire the
        # authoritative clip from WordPress rather than lose the source when
        # the physical worker's temporary download is removed.
        url=str(native.get("source_video_url") or "")
        u=urllib.parse.urlsplit(url)
        if u.scheme!="https" or u.hostname not in ("anthares.us","www.anthares.us") or not u.path.startswith("/wp-content/uploads/anthares-clips/") or not u.path.endswith(".mp4"):
            raise RuntimeError("KWAI_SOURCE_FILE_UNAVAILABLE")
        import atexit
        fd,p=tempfile.mkstemp(prefix="kwai-proof-source-",suffix=".mp4")
        os.close(fd)
        source=pathlib.Path(p)
        atexit.register(lambda:source.unlink(missing_ok=True))
        proc=subprocess.run(["curl.exe","--fail","--location","--silent","--show-error",
            "--connect-timeout","8","--max-time","75","--output",str(source),url],
            capture_output=True,text=True,timeout=85)
        if proc.returncode or not source.is_file() or source.stat().st_size<200000:
            raise RuntimeError("KWAI_SOURCE_RECOVERY_DOWNLOAD_FAILED")
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    if sha!=native.get('media_sha256'):
        raise RuntimeError('KWAI_SOURCE_HASH_MISMATCH')
    caption=native['caption']
    caption_optional=bool(native.get('caption_optional') is True and caption=='')
    with tempfile.TemporaryDirectory(prefix='kwai-public-readback-') as temporary:
        work=pathlib.Path(temporary)
        short=str(native.get("verified_short_url") or "")
        short_public_page_url=None
        candidates=[]
        if short:
            m=re.fullmatch(r"https://k\.kwai\.com/p/[A-Za-z0-9_-]{5,100}",short)
            if not m:raise RuntimeError("KWAI_STORED_SHORT_LINK_INVALID")
            curl=subprocess.run(["curl.exe","--location","--silent","--show-error",
               "--max-time","23","-o","NUL","-w","%{url_effective}",short],
               capture_output=True,text=True,timeout=30)
            if curl.returncode:raise RuntimeError("KWAI_SHORT_LINK_RESOLUTION_FAILED")
            u=urllib.parse.urlsplit(curl.stdout.strip())
            video=re.fullmatch(r"/@"+re.escape(ACCOUNT)+r"/video/([0-9]{16,21})",u.path)
            pars=urllib.parse.parse_qs(u.query)
            if (u.scheme!="https" or u.hostname!="www.kwai.com" or not video or
                pars.get("photoId")!=[video.group(1)] or
                pars.get("authorKwaiId")!=[ACCOUNT]):
                raise RuntimeError("KWAI_SHORT_LINK_PUBLIC_AUTHOR_MISMATCH")
            receipt=int(pars.get("timestamp",["0"])[0])
            short_public_page_url=curl.stdout.strip()
            if native.get("share_receipt_epoch_ms")!=receipt:
                raise RuntimeError("KWAI_KWAI_RECEIPT_IDENTITY_CHANGED")
            if receipt<native["publication_attempted_at"]*1000:
                raise RuntimeError("KWAI_SHARE_RECEIPT_PREDATES_PUBLICATION")
            # The actual app's published-at minute was independently read on
            # the exact posted video before opening its share UI. A short
            # link copied later is an observation time, not upload time.
            from zoneinfo import ZoneInfo
            stamp=str((native.get("profile_verification") or {}).get("post_time") or "")
            when=datetime.datetime.strptime(stamp,"%Y-%m-%d %I:%M %p")
            observed=int(when.replace(tzinfo=ZoneInfo("America/Campo_Grande")).timestamp()*1000)
            if abs(observed-native["publication_attempted_at"]*1000)>10*60*1000:
                raise RuntimeError("KWAI_PHONE_PUBLISHED_TIME_OUTSIDE_START")
            candidates=[(video.group(1),observed)]
        else:
            fetch(PROFILE+'?'+urllib.parse.urlencode({'t':int(time.time()*1000)}),work/'profile.html')
            candidates=read_profile(work/'profile.html',native)
        qualified=[]
        for photo_id,post_ms in candidates[:8]:
            player=PLAYER+photo_id
            page=work/(photo_id+'.html')
            try:
                # The canonical URL can serve a generic fallback before the
                # indexed profile catches up. Kwai's own short-share redirect
                # includes the exact public post author/photo context.
                fetch(short_public_page_url if short_public_page_url else player,page,seconds=20)
                body=page.read_text(encoding='utf-8')
                if (attrs(body,'og:url')==player and (caption_optional or attrs(body,'og:title')==caption)
                    and ('@'+ACCOUNT+')' in attrs(body,'description'))):
                    url=video_link(body)
                else:
                    # The official post page can lag while the same author's
                    # public profile feed already contains this precise media.
                    # Require exact author, public caption, photo ID and time.
                    from kwai_public_feed_proof import get_feed
                    rows=[r for r in get_feed(30) if r.get('photo_id')==photo_id
                         and r.get('account')==ACCOUNT
                         and bool(str(r.get('author') or '').strip())
                         and (caption_optional or r.get('caption')==caption)
                         and abs(int(r.get('created_ms') or 0)-post_ms)<10*60*1000]
                    if len(rows)!=1:
                        raise RuntimeError('KWAI_PUBLIC_FEED_IDENTITY_NOT_UNIQUE')
                    url=str(rows[0]['media_url'])
                publicfile=work/(photo_id+'.mp4')
                fetch(url,publicfile,seconds=72)
                match=compare(source,publicfile)
                qualified.append((photo_id,post_ms,match,hashlib.sha256(publicfile.read_bytes()).hexdigest(),
                                  publicfile.stat().st_size))
            except (OSError,RuntimeError,ValueError) as exc:
                print('KWAI_PUBLIC_CANDIDATE_EXCLUDED='+photo_id+' '+type(exc).__name__,flush=True)
        if len(qualified)!=1:raise RuntimeError('KWAI_PUBLIC_VIDEO_UNIQUE_SOURCE_MATCH_REQUIRED:'+str(len(qualified)))
        photo_id,post_ms,match,public_sha,public_size=qualified[0]
        now=int(time.time()*1000)
        if (not short and now-post_ms>45*60*1000) or abs(post_ms-native['publication_attempted_at']*1000)>10*60*1000:
            raise RuntimeError('KWAI_PUBLIC_POST_TIME_OUTSIDE_PHYSICAL_START')
        permalink=PLAYER+photo_id
        proof={'kind':'kwai_verified_public_media_v2','schema':'kwai-public-media-proof-v2',
               'method':PUBLIC_METHOD,'job_id':jobid,'ok':True,'expected_account':ACCOUNT,
               'actual_author_handle':ACCOUNT,'public_url':permalink,'official_permalink':permalink,
               'photo_id':photo_id,'caption':caption,'caption_optional':caption_optional,'media_sha256':sha,'public_media_sha256':public_sha,
               'source_media_bytes':source.stat().st_size,'public_media_bytes':public_size,
               'public_post_timestamp_ms':post_ms,'verified_at_epoch_ms':now,
               'share_receipt_epoch_ms':native.get('share_receipt_epoch_ms') if short else None,
               'mobile_post_timestamp_source':'physical_kwai_detail_post_time_exact_minute' if short else 'public_profile_feed_timestamp',
               'author_verified_on_external_website':True,'media_match':match}
        evidence_dir=EVID/(re.sub(r'[^A-Za-z0-9._-]+','_',jobid)[-100:])
        evidence_dir.mkdir(parents=True,exist_ok=True)
        dest=evidence_dir/'public-link-proof.json'
        if dest.exists():raise RuntimeError('KWAI_PUBLIC_PROOF_ALREADY_EXISTS')
        native['source_media_sha256']=sha
        native['public_url']=permalink
        stage=dest.with_suffix('.tmp')
        stage.write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf8')
        stage.replace(dest)
        tmp=statepath.with_suffix('.tmp')
        tmp.write_text(json.dumps(native,ensure_ascii=False,indent=2),encoding='utf8')
        tmp.replace(statepath)
        print('KWAI_PUBLIC_VIDEO_PROVEN job='+jobid+' url='+permalink+
              ' inliers='+str(match['inliers'][:2]),flush=True)
        return 0

if __name__=='__main__':
    try:
        if len(sys.argv) not in (2,3):raise RuntimeError('usage: kwai_physical_public_proof.py JOB_ID [SOURCE_FILE]')
        raise SystemExit(recover(sys.argv[1],sys.argv[2] if len(sys.argv)==3 else None))
    except Exception as exc:
        print('KWAI_PHYSICAL_DIRECT_PROOF_PENDING '+type(exc).__name__+':'+str(exc)[:240],flush=True)
        raise SystemExit(75)

