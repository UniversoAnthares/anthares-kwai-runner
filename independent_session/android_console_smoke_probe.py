#!/usr/bin/env python3
"""Twenty distinct checks of the actual Android console smoke requirements."""
import json, os, sys, urllib.request, urllib.error
url=os.environ["ANTHARES_PUBLIC_URL"].rstrip("/")
token=os.environ["ANTHARES_BRIDGE_TOKEN"]
i=int(sys.argv[1])
def request(path,method="GET",payload=None,auth=True):
 h={}
 if auth:h["Authorization"]="Bearer "+token
 data=None
 if payload is not None:h["Content-Type"]="application/json";data=json.dumps(payload).encode()
 req=urllib.request.Request(url+path,data=data,headers=h,method=method)
 try:
  with urllib.request.urlopen(req,timeout=12) as r:return r.status,r.headers.get_content_type(),r.read()
 except urllib.error.HTTPError as e:return e.code,e.headers.get_content_type(),e.read()
tests=[
("public_https_health_and_real_adb",lambda:(lambda r:r[0]==200 and json.loads(r[2]).get("adb_online") is True)(request("/health"))),
("public_screenshot_png_magic",lambda:(lambda r:r[0]==200 and r[1]=="image/png" and r[2].startswith(b"\x89PNG\r\n\x1a\n"))(request("/screen"))),
("missing_auth_rejected",lambda:request("/health",auth=False)[0]==401),
("wrong_auth_rejected",lambda:request("/screen",auth=False)[0]==401),
("home_key_forwarded",lambda:request("/input","POST",{"action":"key","key":"HOME"})[0]==200),
("back_key_forwarded",lambda:request("/input","POST",{"action":"key","key":"BACK"})[0]==200),
("enter_key_forwarded",lambda:request("/input","POST",{"action":"key","key":"ENTER"})[0]==200),
("tab_key_forwarded",lambda:request("/input","POST",{"action":"key","key":"TAB"})[0]==200),
("up_key_forwarded",lambda:request("/input","POST",{"action":"key","key":"DPAD_UP"})[0]==200),
("down_key_forwarded",lambda:request("/input","POST",{"action":"key","key":"DPAD_DOWN"})[0]==200),
("left_key_forwarded",lambda:request("/input","POST",{"action":"key","key":"DPAD_LEFT"})[0]==200),
("right_key_forwarded",lambda:request("/input","POST",{"action":"key","key":"DPAD_RIGHT"})[0]==200),
("tap_forwarded_to_device",lambda:request("/input","POST",{"action":"tap","x":300,"y":400})[0]==200),
("swipe_forwarded_to_device",lambda:request("/input","POST",{"action":"swipe","x1":100,"y1":100,"x2":350,"y2":350})[0]==200),
("unsupported_key_rejected",lambda:request("/input","POST",{"action":"key","key":"POWER"})[0]==400),
("negative_tap_rejected",lambda:request("/input","POST",{"action":"tap","x":-1,"y":20})[0]==400),
("out_of_range_tap_rejected",lambda:request("/input","POST",{"action":"tap","x":10001,"y":20})[0]==400),
("float_coordinates_rejected",lambda:request("/input","POST",{"action":"tap","x":2.5,"y":20})[0]==400),
("shell_injection_rejected",lambda:request("/input","POST",{"action":"shell","command":"id"})[0]==400),
("screen_still_available_after_control",lambda:(lambda a,b:a[0]==200 and b[0]==200 and b[2].startswith(b"\x89PNG\r\n\x1a\n"))(request("/input","POST",{"action":"key","key":"HOME"}),request("/screen"))),
]
name,fn=tests[i-1]
try: ok=bool(fn())
except Exception as e: ok=False; print("PROBE_ERROR="+type(e).__name__,flush=True)
print(f"ANDROID_CONSOLE_SMOKE_{i:02d}_{name}={'PASS' if ok else 'FAIL'}",flush=True)
sys.exit(0 if ok else 1)
