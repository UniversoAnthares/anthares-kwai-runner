#!/usr/bin/env python3
"""Offline normalizer for Anthares six-hour prerecorded HLS.

Process existing TS segments one time into four timestamp-stable MP4 parts.
Runs without RTMP credentials and never changes the active transmitter.
"""
import os,sys,subprocess,pathlib,json,time,hashlib,fcntl
V=pathlib.Path('/home/u566597497/domains/anthares.us/public_html/wp-content/uploads/anthares-live-static/vod/index.m3u8')
R=pathlib.Path('/home/u566597497/.anthares-tiktok-restream')
D=R/'normalized'
F='/home/u566597497/bin/ffmpeg-static/ffmpeg'
P='/home/u566597497/bin/ffmpeg-static/ffprobe'
state=D/'build-state.json'
def report(stage,info=None):
    obj={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'stage':stage}
    if info:obj.update(info)
    temp=D/('.state-'+str(os.getpid()))
    temp.write_text(json.dumps(obj,sort_keys=True)+'\n')
    os.chmod(str(temp),0o600)
    os.rename(str(temp),str(state))
    print('BUILD_STATE '+json.dumps(obj,sort_keys=True),flush=True)
def parse_parts():
    lines=V.read_text().splitlines()
    chunks=[];segs=[];seconds=0.0
    for k,line in enumerate(lines):
        if line.startswith('#EXT-X-DISCONTINUITY'):
            if segs:chunks.append((segs,seconds));segs=[];seconds=0.
        elif line.startswith('#EXTINF:'):
            secs=float(line.split(':',1)[1].split(',',1)[0])
            uri=lines[k+1].strip()
            if not uri.endswith('.ts') or '/' in uri or '\\' in uri or '..' in uri:raise RuntimeError('SOURCE_URI_UNSAFE')
            f=V.parent/uri
            if not f.is_file():raise RuntimeError('SEGMENT_MISSING')
            segs.append((secs,f))
            seconds+=secs
    if segs:chunks.append((segs,seconds))
    if len(chunks)!=4 or abs(sum(x[1] for x in chunks)-22716)>30:
        raise RuntimeError('SOURCE_CHANGED')
    return chunks
def probe(path):
    cmd=[P,'-v','error','-show_entries','format=duration,size:stream=codec_name,codec_type','-of','json',str(path)]
    proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=15)
    if proc.returncode:raise RuntimeError('PROBE_FAILED')
    data=json.loads(proc.stdout)
    streams={(x.get('codec_type'),x.get('codec_name')) for x in data.get('streams',[])}
    if ('video','h264') not in streams or ('audio','aac') not in streams:raise RuntimeError('CODEC_MISMATCH')
    return float(data['format']['duration']),int(data['format']['size'])
def main():
    D.mkdir(mode=0o700,exist_ok=True)
    lock=(D/'builder.lock').open('a')
    fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    os.nice(15)
    chunks=parse_parts()
    digest=hashlib.sha256(V.read_bytes()).hexdigest()
    report('source_checked',{'segments':sum(len(c[0]) for c in chunks),'sha256':digest})
    verified=[]
    for i,(segments,expected) in enumerate(chunks):
        playlist=D/('chunk-'+str(i)+'.m3u8')
        content=['#EXTM3U','#EXT-X-VERSION:6','#EXT-X-TARGETDURATION:12','#EXT-X-MEDIA-SEQUENCE:0','#EXT-X-PLAYLIST-TYPE:VOD','#EXT-X-INDEPENDENT-SEGMENTS']
        for length,f in segments:content.extend(['#EXTINF:{:.6f},'.format(length),str(f)])
        content.append('#EXT-X-ENDLIST')
        playlist.write_text('\n'.join(content)+'\n')
        os.chmod(str(playlist),0o600)
        dest=D/('part-'+str(i)+'.mp4')
        if dest.exists():
            dur,size=probe(dest)
            if abs(dur-expected)>60:raise RuntimeError('OLD_PART_DURATION_MISMATCH')
            report('part_already_verified',{'index':i,'duration':round(dur,2),'size':size})
            verified.append((dest,dur,size))
            continue
        build=D/('part-'+str(i)+'.build')
        if build.exists():build.unlink()
        progress=D/('part-'+str(i)+'.progress')
        err=D/('part-'+str(i)+'.stderr')
        cmd=[F,'-y','-nostdin','-hide_banner','-loglevel','error','-fflags','+genpts','-i',str(playlist),
             '-map','0:v:0','-map','0:a:0','-c:v','copy','-c:a','aac',
             '-af','aresample=async=1:first_pts=0,asetpts=N/SR/TB','-b:a','128k','-ar','44100',
             '-avoid_negative_ts','make_zero','-movflags','+faststart','-f','mp4',
             '-progress',str(progress),str(build)]
        report('encoding_part',{'index':i,'expected_duration':round(expected,2)})
        with err.open('w') as log:
            p=subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=log,timeout=2400)
        if p.returncode:
            report('failed',{'index':i,'exit_code':p.returncode})
            raise RuntimeError('ENCODER_FAILED_{}'.format(i))
        dur,size=probe(build)
        if abs(dur-expected)>60:
            report('failed',{'index':i,'duration':round(dur,2)})
            raise RuntimeError('OUTPUT_DURATION_MISMATCH')
        os.chmod(str(build),0o600)
        os.rename(str(build),str(dest))
        verified.append((dest,dur,size))
        report('part_verified',{'index':i,'duration':round(dur,2),'size':size})
    tmp=D/'.show-staging.ffconcat'
    tmp.write_text('ffconcat version 1.0\n'+''.join('file '+str(f)+'\nduration {:.6f}\n'.format(d) for f,d,_ in verified))
    os.chmod(str(tmp),0o600)
    os.rename(str(tmp),str(D/'show.ffconcat'))
    duration=sum(d for _,d,_ in verified)
    for i in range(3):
        offset=sum(d for _,d,_ in verified[:i+1])-25
        cmd=[F,'-y','-nostdin','-hide_banner','-loglevel','warning',
             '-ss','{:.3f}'.format(offset),'-f','concat','-safe','0',
             '-i',str(D/'show.ffconcat'),'-t','85','-c:v','copy','-c:a','copy',
             '-avoid_negative_ts','make_zero','-f','flv','-progress','pipe:1','/dev/null']
        p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=90)
        stderr=p.stderr.lower()
        if p.returncode or 'progress=end' not in p.stdout or any(x in stderr for x in ('packet is missing pts','error muxing','error submitting','invalid argument')):
            report('failed_concat',{'index':i,'exit_code':p.returncode})
            raise RuntimeError('FULL_BOUNDARY_FAILED_{}'.format(i))
        report('concat_boundary_verified',{'index':i,'offset':round(offset,2)})
    report('READY',{'total_duration':round(duration,2),'bytes':sum(s for _,_,s in verified),'manifest_sha256':digest})
if __name__=='__main__':
    try:main()
    except Exception as e:
        print('NORMALIZER_FAILURE='+type(e).__name__+':'+str(e)[:100],flush=True)
        sys.exit(1)

