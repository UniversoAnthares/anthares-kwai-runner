#!/usr/bin/env python3
"""Canonical Anthares short-video layout for legacy horizontal Instagram media.

Matches the existing CORTES editorial geometry: 720x1280 portrait,
150px headline, 1080px presenter panels, 50px footer; navy, cyan accent.
Face-count inference is conservative: only verified source lanes are split.
"""
from __future__ import annotations

import io
import re
import subprocess
from pathlib import Path

WIDTH, HEIGHT = 720, 1280
HEADER, BODY, FOOTER = 150, 1080, 50
LAYOUT_REV = "anthares-portrait-layout-v2"


def lanes_from_centres(centres: list[tuple[float, float]]) -> int:
    """Return 1,2,3 or 4; never assume a panel absent clear facial geometry."""
    if not 1 <= len(centres) <= 4:
        return 1
    if len(centres) == 2:
        return 2 if sorted(int(x > 0.5) for x,y in centres)==[0,1] and all(
            x < .44 or x > .56 for x,y in centres) else 1
    if len(centres) == 3:
        thirds=[min(2,int(x*3)) for x,y in centres]
        return 3 if sorted(thirds)==[0,1,2] else 1
    if len(centres) == 4:
        slots={(int(x>=0.5),int(y>=0.5)) for x,y in centres}
        return 4 if len(slots)==4 else 1
    return 1


def discover_layout(source: Path, ffmpeg: str) -> int:
    """OpenCV face evidence from source frames; unavailable detection means single."""
    try:
        import cv2
        import numpy as np
        root=Path(cv2.data.haarcascades)
        cascade=cv2.CascadeClassifier(str(root/'haarcascade_frontalface_default.xml'))
        if cascade.empty():
            return 1
    except (ImportError, AttributeError, OSError):
        return 1
    votes=[]
    for second in (2, 8, 16, 26):
        try:
            run=subprocess.run([ffmpeg,'-nostdin','-hide_banner','-loglevel','error',
                  '-ss',str(second),'-i',str(source),'-frames:v','1',
                  '-f','image2pipe','-vcodec','png','pipe:1'],
                  capture_output=True,timeout=25,check=True)
            frame=cv2.imdecode(np.frombuffer(run.stdout,dtype=np.uint8),cv2.IMREAD_COLOR)
            if frame is None:
                continue
            h,w=frame.shape[:2]
            if w < 640 or w/h < 1.2:
                continue
            gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            boxes=cascade.detectMultiScale(gray,scaleFactor=1.08,minNeighbors=6,
                                           minSize=(max(30,int(h*.06)),)*2)
            centres=[((x+bw/2)/w,(y+bh/2)/h) for x,y,bw,bh in boxes
                     if bw*bh>=w*h*.0015]
            votes.append(lanes_from_centres(centres))
        except (subprocess.SubprocessError,ValueError,AttributeError):
            continue
    for n in (4,3,2):
        if votes.count(n)>=2:
            return n
    return 1


def layout_filter(presenters: int) -> str:
    if presenters == 2:
        chain=("[0:v]split=2[left][right];"
          "[left]crop=iw/2:ih:0:0,scale=720:540:force_original_aspect_ratio=increase,"
          "crop=720:540,setsar=1[top];"
          "[right]crop=iw/2:ih:iw/2:0,scale=720:540:force_original_aspect_ratio=increase,"
          "crop=720:540,setsar=1[bottom];"
          "[top][bottom]vstack=inputs=2[body];")
    elif presenters == 3:
        chain=("[0:v]split=3[a][b][c];"
          "[a]crop=iw/3:ih:0:0,scale=720:360:force_original_aspect_ratio=increase,"
          "crop=720:360,setsar=1[p0];"
          "[b]crop=iw/3:ih:iw/3:0,scale=720:360:force_original_aspect_ratio=increase,"
          "crop=720:360,setsar=1[p1];"
          "[c]crop=iw/3:ih:2*iw/3:0,scale=720:360:force_original_aspect_ratio=increase,"
          "crop=720:360,setsar=1[p2];"
          "[p0][p1][p2]vstack=inputs=3[body];")
    elif presenters == 4:
        chain=("[0:v]split=4[a][b][c][d];"
          "[a]crop=iw/2:ih/2:0:0,scale=360:540:force_original_aspect_ratio=increase,"
          "crop=360:540,setsar=1[p0];"
          "[b]crop=iw/2:ih/2:iw/2:0,scale=360:540:force_original_aspect_ratio=increase,"
          "crop=360:540,setsar=1[p1];"
          "[c]crop=iw/2:ih/2:0:ih/2,scale=360:540:force_original_aspect_ratio=increase,"
          "crop=360:540,setsar=1[p2];"
          "[d]crop=iw/2:ih/2:iw/2:ih/2,scale=360:540:force_original_aspect_ratio=increase,"
          "crop=360:540,setsar=1[p3];"
          "[p0][p1]hstack=inputs=2[row0];"
          "[p2][p3]hstack=inputs=2[row1];"
          "[row0][row1]vstack=inputs=2[body];")
    else:
        chain=("[0:v]scale=720:1080:force_original_aspect_ratio=decrease,"
             "pad=720:1080:(ow-iw)/2:(oh-ih)/2:color=0x0D1322,setsar=1[body];")
    return (chain+"[body]pad=720:1280:0:150:color=0x0D1322[canvas];"
            "[canvas][1:v]overlay=0:0:shortest=1:format=auto,"
            "format=yuv420p[v]")


def overlay_title(title: str, dest: Path, presenters: int) -> None:
    from PIL import Image, ImageDraw, ImageFont
    im=Image.new('RGBA',(WIDTH,HEIGHT),(0,0,0,0))
    draw=ImageDraw.Draw(im)
    bg=(13,19,34,255)
    accent=(61,177,252,255)
    draw.rectangle((0,0,WIDTH,HEADER-1),fill=bg)
    draw.rectangle((0,HEIGHT-FOOTER,WIDTH,HEIGHT),fill=bg)
    draw.rectangle((23,20,29,HEADER-15),fill=accent)
    if presenters in (2,3):
        for i in range(1,presenters):
            at=HEADER+(BODY//presenters)*i
            draw.rectangle((0,at-4,WIDTH,at+4),fill=accent)
    if presenters==4:
        draw.rectangle((0,HEADER+BODY//2-4,WIDTH,HEADER+BODY//2+4),fill=accent)
        draw.rectangle((WIDTH//2-4,HEADER,WIDTH//2+4,HEIGHT-FOOTER),fill=accent)
    def font(size:int):
        for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                  '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf'):
            if Path(p).is_file():
                return ImageFont.truetype(p,size=size)
        return ImageFont.load_default()
    words=re.sub(r'\\s+',' ',str(title or 'Universo Anthares')).strip().split()
    f=font(43)
    lines=[]
    current=''
    for w in words:
        proposal=(current+' '+w).strip()
        if draw.textbbox((0,0),proposal,font=f)[2]<=640:
            current=proposal
        else:
            if current:
                lines.append(current)
            current=w
    if current:
        lines.append(current)
    if len(lines)>2:
        lines=lines[:2]
        while lines[1] and draw.textbbox((0,0),lines[1]+'…',font=f)[2]>640:
            lines[1]=lines[1][:-1]
        lines[1]+='…'
    for i,line in enumerate(lines[:2]):
        draw.text((49,24+60*i),line,font=f,fill=(250,251,255,255))
    draw.text((26,1236),'UNIVERSO ANTHARES   •   anthares.us',
              font=font(23),fill=(220,231,243,255))
    im.save(dest)


def render_standard(source: Path,target: Path,title: str,ffmpeg: str) -> int:
    presenters=discover_layout(source,ffmpeg)
    art=target.with_name(target.stem+'.art.png')
    try:
        overlay_title(title,art,presenters)
        subprocess.run([ffmpeg,'-nostdin','-y','-hide_banner','-loglevel','error',
          '-i',str(source),'-loop','1','-i',str(art),
          '-filter_complex',layout_filter(presenters),'-map','[v]','-map','0:a:0?',
          '-t','90','-r','30','-c:v','libx264','-preset','veryfast',
          '-crf','23','-pix_fmt','yuv420p','-c:a','aac','-b:a','96k',
          '-movflags','+faststart',str(target)],check=True,capture_output=True,
          timeout=420)
        return presenters
    finally:
        art.unlink(missing_ok=True)
