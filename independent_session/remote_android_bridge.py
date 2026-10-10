#!/usr/bin/env python3
"""Minimal authenticated ADB bridge for the Anthares remote Android UI.
Binds localhost by default. Do not expose publicly without an authenticated TLS tunnel.
"""
import base64, hashlib, json, os, secrets, socket, struct, subprocess, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

TOKEN=os.environ.get("ANTHARES_BRIDGE_TOKEN","")
HOST=os.environ.get("ANTHARES_BRIDGE_HOST","127.0.0.1")
PORT=int(os.environ.get("ANTHARES_BRIDGE_PORT","8765"))
MAX_BODY=4096
if len(TOKEN)<32:
    raise SystemExit("BRIDGE_REFUSED: set ANTHARES_BRIDGE_TOKEN to a random secret of at least 32 characters")
def adb(*args, timeout=8):
    p=subprocess.run(["adb",*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    if p.returncode: raise RuntimeError("ADB_COMMAND_FAILED")
    return p.stdout
class Handler(BaseHTTPRequestHandler):
    server_version="AntharesBridge/1"
    def log_message(self,*a): pass
    def _json(self,code,obj):
        data=json.dumps(obj,separators=(",",":")).encode()
        self.send_response(code);self.send_header("Content-Type","application/json");self.send_header("Cache-Control","no-store");self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)
    def _auth(self):
        supplied=self.headers.get("Authorization","")
        return secrets.compare_digest(supplied,"Bearer "+TOKEN)
    def do_GET(self):
        if not self._auth(): return self._json(401,{"error":"UNAUTHORIZED"})
        route=urlparse(self.path).path
        try:
            if route=="/health":
                devices=adb("devices").decode(errors="replace").splitlines()[1:]
                online=any(x.split()[-1:]==["device"] for x in devices if x.strip())
                return self._json(200,{"service":"anthares-bridge","adb_online":online})
            if route=="/screen":
                png=adb("exec-out","screencap","-p",timeout=8)
                self.send_response(200);self.send_header("Content-Type","image/png");self.send_header("Cache-Control","no-store");self.send_header("Content-Length",str(len(png)));self.end_headers();self.wfile.write(png);return
            return self._json(404,{"error":"NOT_FOUND"})
        except Exception: return self._json(503,{"error":"DEVICE_UNAVAILABLE"})
    def do_POST(self):
        if not self._auth(): return self._json(401,{"error":"UNAUTHORIZED"})
        if urlparse(self.path).path!="/input": return self._json(404,{"error":"NOT_FOUND"})
        try:
            n=int(self.headers.get("Content-Length","0"))
            if n<1 or n>MAX_BODY: return self._json(413,{"error":"BODY_SIZE"})
            body=json.loads(self.rfile.read(n))
            action=body.get("action")
            if action=="tap":
                x,y=body.get("x"),body.get("y")
                if type(x) is not int or type(y) is not int or not(0<=x<=10000 and 0<=y<=10000): return self._json(400,{"error":"INVALID_COORDINATES"})
                adb("shell","input","tap",str(x),str(y))
            elif action=="swipe":
                vals=[body.get(k) for k in ("x1","y1","x2","y2")]
                if any(type(v) is not int or not 0<=v<=10000 for v in vals): return self._json(400,{"error":"INVALID_COORDINATES"})
                adb("shell","input","swipe",*map(str,vals),"350")
            elif action=="key":
                key=body.get("key")
                if key not in {"BACK","HOME","ENTER","TAB","DPAD_UP","DPAD_DOWN","DPAD_LEFT","DPAD_RIGHT"}: return self._json(400,{"error":"KEY_NOT_ALLOWED"})
                adb("shell","input","keyevent",{"BACK":"4","HOME":"3","ENTER":"66","TAB":"61","DPAD_UP":"19","DPAD_DOWN":"20","DPAD_LEFT":"21","DPAD_RIGHT":"22"}[key])
            else: return self._json(400,{"error":"ACTION_NOT_ALLOWED"})
            return self._json(200,{"ok":True})
        except Exception: return self._json(503,{"error":"DEVICE_UNAVAILABLE"})
def main():
    print("ANTHARES_BRIDGE_LISTENING="+HOST+":"+str(PORT),flush=True)
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
if __name__=="__main__": main()
