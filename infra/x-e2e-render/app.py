#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from flask import Flask, jsonify, send_file

from anthares_microcut_v2 import run as microcut_run
from generate_microcut_fixture import main as _unused_main

ROOT = Path('/tmp/anthares-x-e2e')
RAW = ROOT / 'raw.mp4'
MICRO = ROOT / 'microcut.mp4'
FINAL = ROOT / 'final.mp4'
REPORT = ROOT / 'report.json'
READY = False
ERROR = ''
REPORT_DATA = {}

app = Flask(__name__)


def generate():
    global READY, ERROR, REPORT_DATA
    try:
        ROOT.mkdir(parents=True, exist_ok=True)
        subprocess.run(['python','/app/generate_microcut_fixture.py',str(RAW)], check=True, timeout=180)
        REPORT_DATA = microcut_run(RAW, MICRO)
        REPORT.write_text(json.dumps(REPORT_DATA,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        reasons = REPORT_DATA.get('reasons') or {}
        assert float(REPORT_DATA.get('removed_seconds') or 0) >= 0.18
        assert int(REPORT_DATA.get('intervals') or 0) >= 1
        assert reasons.get('silence',0) >= 1
        assert sum(reasons.get(k,0) for k in ('immediate_repetition','fuzzy_restart','stutter','filler')) >= 1
        subprocess.run([
            'ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(MICRO),
            '-vf','scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,format=yuv420p',
            '-c:v','libx264','-preset','veryfast','-crf','19','-c:a','aac','-b:a','160k','-movflags','+faststart',str(FINAL)
        ],check=True,timeout=300)
        if not FINAL.is_file() or FINAL.stat().st_size < 250_000:
            raise RuntimeError('final media missing or too small')
        READY = True
    except Exception as exc:
        ERROR = f'{type(exc).__name__}: {exc}'
        READY = False


@app.get('/')
@app.get('/health')
def health():
    return jsonify(ok=True,ready=READY,error=ERROR,report={k:v for k,v in REPORT_DATA.items() if k!='transcript'})


@app.get('/report.json')
def report():
    if not READY:
        return jsonify(ok=False,error=ERROR),503
    return jsonify(REPORT_DATA)


@app.get('/final.mp4')
def final():
    if not READY:
        return jsonify(ok=False,error=ERROR),503
    return send_file(FINAL,mimetype='video/mp4',as_attachment=False,conditional=True)


generate()
port=int(os.getenv('PORT','10000'))
app.run(host='0.0.0.0',port=port)
