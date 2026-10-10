#!/usr/bin/env python3
"""One distinct acceptance probe against a real HTTPS quick tunnel and authenticated bridge."""
import json, os, sys, urllib.error, urllib.request
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
  with urllib.request.urlopen(req,timeout=10) as r:return r.status,r.headers.get("Content-Type",""),r.read()
 except urllib.error.HTTPError as e:return e.code,e.headers.get("Content-Type",""),e.read()
tests=[
("public_https_health",lambda:(lambda r:r[0]==200 and json.loads(r[2]).get("adb_online") is True)(request("/health"))),
("public_png_screenshot",lambda:(lambda r:r[0]==200 and r[1].startswith("image/png") and r[2].startswith(b"\x89PNG\r\n\x1a\n"))(request("/screen"))),
("unauthenticated_health_denied",lambda:request("/health",auth=False)[0]==401),
("unauthenticated_screen_denied",lambda:request("/screen",auth=False)[0]==401),
("unauthenticated_input_denied",lambda:request("/input","POST",{"action":"key","key":"HOME"},False)[0]==401),
("unknown_route_404",lambda:request("/no-such-route")[0]==404),
("home_key",lambda:request("/input","POST",{"action":"key","key":"HOME"})[0]==200),
("back_key",lambda:request("/input","POST",{"action":"key","key":"BACK"})[0]==200),
("enter_key",lambda:request("/input","POST",{"action":"key","key":"ENTER"})[0]==200),
("tab_key",lambda:request("/input","POST",{"action":"key","key":"TAB"})[0]==200),
("up_key",lambda:request("/input","POST",{"action":"key","key":"DPAD_UP"})[0]==200),
("down_key",lambda:request("/input","POST",{"action":"key","key":"DPAD_DOWN"})[0]==200),
("left_key",lambda:request("/input","POST",{"action":"key","key":"DPAD_LEFT"})[0]==200),
("right_key",lambda:request("/input","POST",{"action":"key","key":"DPAD_RIGHT"})[0]==200),
("tap_forwarded",lambda:request("/input","POST",{"action":"tap","x":500,"y":500})[0]==200),
("swipe_forwarded",lambda:request("/input","POST",{"action":"swipe","x1":200,"y1":200,"x2":300,"y2":300})[0]==200),
("unknown_key_rejected",lambda:request("/input","POST",{"action":"key","key":"POWER"})[0]==400),
("negative_coordinates_rejected",lambda:request("/input","POST",{"action":"tap","x":-1,"y":0})[0]==400),
("non_integer_coordinates_rejected",lambda:request("/input","POST",{"action":"tap","x":1.5,"y":0})[0]==400),
("arbitrary_action_rejected",lambda:request("/input","POST",{"action":"shell","command":"id"})[0]==400),
]
name,fn=tests[i-1]
try: ok=bool(fn())
except Exception as e: ok=False; print("PROBE_EXCEPTION="+type(e).__name__)
print(f"LIVE_BRIDGE_PROBE_{i:02d}_{name}={'PASS' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)
