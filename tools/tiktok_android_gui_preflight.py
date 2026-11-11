#!/usr/bin/env python3
"""Fail closed if cloud scrcpy is not really showing Android pixels in Xvfb.

Samples only the framebuffer's numeric variation. Never saves a screenshot,
sends Android pixels off runner, or logs personally identifying screen text.
"""
import io
import os
import subprocess
import sys
import time
from PIL import Image, ImageStat

def try_screenshot():
    r=subprocess.run(["import","-window","root","png:-"],capture_output=True,timeout=15)
    if r.returncode:raise RuntimeError("X11_FRAME_CAPTURE_FAILED")
    with Image.open(io.BytesIO(r.stdout)) as im:
        image=im.convert("RGB")
        # display should include application window, not a blank X11 root
        colors=image.resize((128,96)).getcolors(128*96)
        distinct=len(colors or [])
        pixels=list(image.resize((128,96)).getdata())
        lit=sum(1 for p in pixels if max(p)>35)
        return distinct, lit/len(pixels)

def main():
    if not os.getenv("DISPLAY"):
        raise RuntimeError("DISPLAY_UNSET")
    for iteration in range(18):
        unique,bright=try_screenshot()
        print(f"TIKTOK_GUI_PREFLIGHT_SAMPLE={iteration+1} COLORS={unique} BRIGHT_PERCENT={round(bright*100)}",flush=True)
        if unique>=20 and bright>=0.05:
            print("TIKTOK_ANDROID_GUI_ACTUAL_PIXELS=PROVEN",flush=True)
            return
        time.sleep(3)
    raise RuntimeError("ANDROID_GUI_BLACK_SCREEN")
if __name__=="__main__":
    try:main()
    except Exception as e:
        code=str(e)
        if code not in {"DISPLAY_UNSET","X11_FRAME_CAPTURE_FAILED","ANDROID_GUI_BLACK_SCREEN"}:
            code="GUI_PREFLIGHT_"+type(e).__name__.upper()
        print("TIKTOK_ANDROID_GUI_PREFLIGHT_FAILED="+code,flush=True)
        sys.exit(1)
