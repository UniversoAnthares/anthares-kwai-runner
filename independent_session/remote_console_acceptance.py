#!/usr/bin/env python3
"""One focused authenticated remote-console acceptance test per matrix job."""
import json, os, sys, urllib.error, urllib.request
base="http://127.0.0.1:8765"
token=os.environ["ANTHARES_BRIDGE_TOKEN"]
case=int(sys.argv[1])
def req(path, method="GET", payload=None, auth=True):
 headers={}
 if auth: headers["Authorization"]="Bearer "+token
 data=None
 if payload is not None:
  data=json.dumps(payload).encode(); headers["Content-Type"]="application/json"
 r=urllib.request.Request(base+path,data=data,headers=headers,method=method)
 try:
  with urllib.request.urlopen(r,timeout=10) as x:return x.status,x.headers.get("Content-Type",""),x.read()
 except urllib.error.HTTPError as e:return e.code,e.headers.get("Content-Type",""),e.read()
tests=[
 ("health authorized",lambda: req("/health")[0]==200 and json.loads(req("/health")[2]).get("adb_online") is True),
 ("screen returns PNG",lambda: req("/screen")[0]==200 and req("/screen")[1].startswith("image/png") and req("/screen")[2][:8]==b"\x89PNG\r\n\x1a\n"),
 ("reject missing auth",lambda: req("/health",auth=False)[0]==401),
 ("reject invalid token",lambda: req("/health",auth=False)[0]==401),
 ("unknown route 404",lambda: req("/missing")[0]==404),
 ("key HOME",lambda: req("/input","POST",{"action":"key","key":"HOME"})[0]==200),
 ("key BACK",lambda: req("/input","POST",{"action":"key","key":"BACK"})[0]==200),
 ("key ENTER",lambda: req("/input","POST",{"action":"key","key":"ENTER"})[0]==200),
 ("key TAB",lambda: req("/input","POST",{"action":"key","key":"TAB"})[0]==200),
 ("key DPAD_UP",lambda: req("/input","POST",{"action":"key","key":"DPAD_UP"})[0]==200),
 ("key DPAD_DOWN",lambda: req("/input","POST",{"action":"key","key":"DPAD_DOWN"})[0]==200),
 ("key DPAD_LEFT",lambda: req("/input","POST",{"action":"key","key":"DPAD_LEFT"})[0]==200),
 ("key DPAD_RIGHT",lambda: req("/input","POST",{"action":"key","key":"DPAD_RIGHT"})[0]==200),
 ("tap valid",lambda: req("/input","POST",{"action":"tap","x":500,"y":500})[0]==200),
 ("swipe valid",lambda: req("/input","POST",{"action":"swipe","x1":500,"y1":500,"x2":520,"y2":520})[0]==200),
 ("reject unknown key",lambda: req("/input","POST",{"action":"key","key":"POWER"})[0]==400),
 ("reject negative tap",lambda: req("/input","POST",{"action":"tap","x":-1,"y":2})[0]==400),
 ("reject float coordinates",lambda: req("/input","POST",{"action":"tap","x":1.5,"y":2})[0]==400),
 ("reject unknown action",lambda: req("/input","POST",{"action":"launch_arbitrary_shell"})[0]==400),
 ("screen after input",lambda: req("/input","POST",{"action":"key","key":"HOME"})[0]==200 and req("/screen")[2][:8]==b"\x89PNG\r\n\x1a\n"),
]
name,fn=tests[case-1]
try: ok=bool(fn())
except Exception as e: ok=False; print("TEST_EXCEPTION="+type(e).__name__)
print(f"ANTHARES_REMOTE_CONSOLE_TEST_{case:02d}={'PASS' if ok else 'FAIL'} name={name}")
sys.exit(0 if ok else 1)
