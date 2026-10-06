#!/usr/bin/env python3
"""Read-only hidden-desktop probe for Grok, Manus and Perplexity.

No prompt is sent. Each provider gets its own dedicated Chrome profile.
"""
import ctypes, ctypes.wintypes as wt
import json, os, socket, subprocess, time, uuid, urllib.request
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = r"C:\Users\Lucas\AntharesWork"
PROVIDERS = {
    "grok": {"url": "https://grok.com/", "profile": os.path.join(BASE, "grok-hidden-desktop-profile")},
    "manus": {"url": "https://manus.im/", "profile": os.path.join(BASE, "manus-hidden-desktop-profile")},
    "perplexity": {"url": "https://www.perplexity.ai/", "profile": os.path.join(BASE, "perplexity-hidden-desktop-profile")},
}

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32 = ctypes.WinDLL("user32", use_last_error=True)
class STARTUPINFO(ctypes.Structure):
    _fields_=[('cb',wt.DWORD),('lpReserved',wt.LPWSTR),('lpDesktop',wt.LPWSTR),('lpTitle',wt.LPWSTR),('dwX',wt.DWORD),('dwY',wt.DWORD),('dwXSize',wt.DWORD),('dwYSize',wt.DWORD),('dwXCountChars',wt.DWORD),('dwYCountChars',wt.DWORD),('dwFillAttribute',wt.DWORD),('dwFlags',wt.DWORD),('wShowWindow',wt.WORD),('cbReserved2',wt.WORD),('lpReserved2',ctypes.POINTER(ctypes.c_byte)),('hStdInput',wt.HANDLE),('hStdOutput',wt.HANDLE),('hStdError',wt.HANDLE)]
class PROCESS_INFORMATION(ctypes.Structure):
    _fields_=[('hProcess',wt.HANDLE),('hThread',wt.HANDLE),('dwProcessId',wt.DWORD),('dwThreadId',wt.DWORD)]
user32.CreateDesktopW.argtypes=[wt.LPCWSTR,wt.LPCWSTR,ctypes.c_void_p,wt.DWORD,wt.DWORD,ctypes.c_void_p]
user32.CreateDesktopW.restype=wt.HANDLE
kernel32.CreateProcessW.argtypes=[wt.LPCWSTR,wt.LPWSTR,ctypes.c_void_p,ctypes.c_void_p,wt.BOOL,wt.DWORD,ctypes.c_void_p,wt.LPCWSTR,ctypes.POINTER(STARTUPINFO),ctypes.POINTER(PROCESS_INFORMATION)]
kernel32.CreateProcessW.restype=wt.BOOL

def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1",0)); return s.getsockname()[1]

def wait_cdp(port, seconds=25):
    end=time.time()+seconds
    while time.time()<end:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version",timeout=1) as r:
                if r.status==200: return f"http://127.0.0.1:{port}"
        except Exception: time.sleep(.5)
    return None

def probe(name, cfg):
    started=time.time(); port=free_port(); desktop="AntharesAI_"+name+"_"+uuid.uuid4().hex[:8]
    hdesk=user32.CreateDesktopW(desktop,None,None,0,0x10000000,None)
    result={"provider":name,"status":None,"title":None,"host":None,"prompt_boxes":0,"login_signals":[],"elapsed_s":None}
    if not hdesk:
        result["status"]="DESKTOP_CREATE_FAILED"; return result
    os.makedirs(cfg["profile"],exist_ok=True)
    cmd=f'"{CHROME}" --remote-debugging-port={port} --remote-allow-origins=* --user-data-dir="{cfg["profile"]}" --no-first-run --no-default-browser-check {cfg["url"]}'
    si=STARTUPINFO(); si.cb=ctypes.sizeof(si); si.lpDesktop=desktop
    pi=PROCESS_INFORMATION(); buf=ctypes.create_unicode_buffer(cmd); pid=None
    try:
        if not kernel32.CreateProcessW(None,buf,None,None,False,0,None,None,ctypes.byref(si),ctypes.byref(pi)):
            result["status"]="CHROME_LAUNCH_FAILED"; return result
        pid=int(pi.dwProcessId); kernel32.CloseHandle(pi.hThread); kernel32.CloseHandle(pi.hProcess)
        endpoint=wait_cdp(port)
        if not endpoint:
            result["status"]="CDP_NOT_READY"; return result
        with sync_playwright() as p:
            browser=p.chromium.connect_over_cdp(endpoint); ctx=browser.contexts[0]; page=ctx.pages[0] if ctx.pages else ctx.new_page()
            time.sleep(8)
            try:
                result["title"]=page.title(); result["host"]=urlparse(page.url).netloc
                body=page.locator("body").inner_text(timeout=3000)
                low=(result["title"]+"\n"+body).lower()
                count=0
                for selector in ["textarea", "div[contenteditable='true']", "input[type='text']"]:
                    try:
                        loc=page.locator(selector)
                        count += sum(1 for i in range(loc.count()) if loc.nth(i).is_visible())
                    except Exception: pass
                result["prompt_boxes"]=count
                login_terms=["sign in","log in","login","entrar","continue with google","continuar com o google","create account","criar conta","sign up"]
                result["login_signals"]=[x for x in login_terms if x in low]
                if any(x in low for x in ["just a moment","um momento","checking your browser","verifying you are human"]):
                    result["status"]="CHALLENGE"
                elif result["login_signals"] and count==0:
                    result["status"]="LOGIN_REQUIRED"
                elif count>0:
                    result["status"]="PROMPT_SURFACE_VISIBLE"
                else:
                    result["status"]="PAGE_NO_PROMPT"
            except Exception as e:
                result["status"]="PROBE_ERROR"; result["error"]=str(e)[:180]
            browser.close()
    finally:
        if pid:
            subprocess.run(["taskkill","/PID",str(pid),"/T","/F"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(.5); user32.CloseDesktop(hdesk); result["elapsed_s"]=round(time.time()-started,2)
    return result

if __name__=="__main__":
    print(json.dumps({"results":[probe(n,c) for n,c in PROVIDERS.items()]},ensure_ascii=False))
