#!/usr/bin/env python3
"""Generate a private continuation playlist for the immutable Anthares HLS show."""
import pathlib,sys,os,time,tempfile,re
src=pathlib.Path(sys.argv[1])
origin=int(pathlib.Path(sys.argv[2]).read_text().strip())
period=int(sys.argv[3])
dst=pathlib.Path(sys.argv[4])
if period < 300 or period > 86400:raise SystemExit('invalid period')
if dst.parent != pathlib.Path('/home/u566597497/.anthares-tiktok-restream'):raise SystemExit('invalid destination')
if not src.is_file():raise SystemExit('source missing')
position=(int(time.time())-origin)%period
remaining=period-position
entries=[]
total=0.0
pending_discontinuity=False
lines=src.read_text().splitlines()
for k,line in enumerate(lines):
 if line.strip()=='#EXT-X-DISCONTINUITY':
  pending_discontinuity=True
 elif line.startswith('#EXTINF:'):
  length=float(line.split(':',1)[1].split(',',1)[0])
  uri=lines[k+1].strip() if k+1<len(lines) else ''
  if not re.match(r'^[A-Za-z0-9._-]+\.ts$',uri):
   raise SystemExit('invalid segment')
  entries.append((total,length,uri,pending_discontinuity))
  total+=length
  pending_discontinuity=False
if total < period+10 or len(entries)<100:raise SystemExit('source too short')
ix=next((j for j,e in enumerate(entries) if e[0]+e[1]>position),None)
if ix is None:raise SystemExit('position missing')
before=sum(int(e[3]) for e in entries[:ix])
head=['#EXTM3U','#EXT-X-VERSION:6','#EXT-X-TARGETDURATION:12',
      '#EXT-X-MEDIA-SEQUENCE:'+str(ix),'#EXT-X-DISCONTINUITY-SEQUENCE:'+str(before),
      '#EXT-X-PLAYLIST-TYPE:VOD','#EXT-X-INDEPENDENT-SEGMENTS']
for start,length,uri,disc in entries[ix:]:
 if disc:head.append('#EXT-X-DISCONTINUITY')
 head.extend(['#EXTINF:{:.6f},'.format(length),str(src.parent/uri)])
head.append('#EXT-X-ENDLIST')
fd,tmp=tempfile.mkstemp(prefix='.seek-continuity-',suffix='.tmp',dir=str(dst.parent))
try:
 os.fchmod(fd,0o600)
 with os.fdopen(fd,'w') as f:
  f.write('\n'.join(head)+'\n')
 os.replace(tmp,str(dst))
finally:
 if os.path.exists(tmp):os.unlink(tmp)
print('{} {:.6f} {}'.format(position,max(0.0,position-entries[ix][0]),remaining))
