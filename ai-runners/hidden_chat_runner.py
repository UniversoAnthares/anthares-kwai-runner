#!/usr/bin/env python3
"""Generic hidden-desktop web chat runner for dedicated provider profiles.

Status: architecture scaffold. Claude has its own PROVEN runner. Grok/Manus/Perplexity
must be bootstrapped and validated before this generic runner is considered PROVEN.
"""
import argparse, ctypes, ctypes.wintypes as wt, json, os, socket, subprocess, time, uuid, urllib.request
from playwright.sync_api import sync_playwright

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = r"C:\Users\Lucas\AntharesWork"
PROVIDERS = {
    "grok": {"url":"https://grok.com/", "profile":os.path.join(BASE,"grok-hidden-desktop-profile")},
    "manus": {"url":"https://manus.im/", "profile":os.path.join(BASE,"manus-hidden-desktop-profile")},
    "perplexity": {"url":"https://www.perplexity.ai/", "profile":os.path.join(BASE,"perplexity-hidden-desktop-profile")},
}
PROMPT_SELECTORS=["textarea","div[contenteditable='true']"]
ASSISTANT_SELECTORS=['[data-testid*="assistant"]','[data-testid*="answer"]','[class*="assistant"]','[class*="answer"]','main article']

kernel32=ctypes.WinDLL("kernel32",use_last_error=True); user32=ctypes.WinDLL("user32",use_last_error=True)
class STARTUPINFO(ctypes.Structure):
    _fields_=[('cb',wt.DWORD),('lpReserved',wt.LPWSTR),('lpDesktop',wt.LPWSTR),('lpTitle',wt.LPWSTR),('dwX',wt.DWORD),('dwY',wt.DWORD),('dwXSize',wt.DWORD),('dwYSize',wt.DWORD),('dwXCountChars',wt.DWORD),('dwYCountChars',wt.DWORD),('dwFillAttribute',wt.DWORD),('dwFlags',wt.DWORD),('wShowWindow',wt.WORD),('cbReserved2',wt.WORD),('lpReserved2',ctypes.POINTER(ctypes.c_byte)),('hStdInput',wt.HANDLE),('hStdOutput',wt.HANDLE),('hStdError',wt.HANDLE)]
class PROCESS_INFORMATION(ctypes.Structure):
    _fields_=[('hProcess',wt.HANDLE),('hThread',wt.HANDLE),('dwProcessId',wt.DWORD),('dwThreadId',wt.DWORD)]
user32.CreateDesktopW.argtypes=[wt.LPCWSTR,wt.LPCWSTR,ctypes.c_void_p,wt.DWORD,wt.DWORD,ctypes.c_void_p]; user32.CreateDesktopW.restype=wt.HANDLE
kernel32.CreateProcessW.argtypes=[wt.LPCWSTR,wt.LPWSTR,ctypes.c_void_p,ctypes.c_void_p,wt.BOOL,wt.DWORD,ctypes.c_void_p,wt.LPCWSTR,ctypes.POINTER(STARTUPINFO),ctypes.POINTER(PROCESS_INFORMATION)]; kernel32.CreateProcessW.restype=wt.BOOL

def free_port():
    with socket.socket() as s: s.bind(("127.0.0.1",0)); return s.getsockname()[1]

def wait_cdp(port,seconds=30):
    end=time.time()+seconds
    while time.time()<end:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version",timeout=1) as r:
                if r.status==200:return f"http://127.0.0.1:{port}"
        except Exception:time.sleep(.5)
    return None

def run(provider,prompt,timeout=90):
    cfg=PROVIDERS[provider]; started=time.time(); port=free_port(); desktop="AntharesChat_"+provider+"_"+uuid.uuid4().hex[:8]
    hdesk=user32.CreateDesktopW(desktop,None,None,0,0x10000000,None); pid=None
    result={"provider":provider,"ok":False,"status":None,"response":"","elapsed_s":None}
    try:
        if not hdesk: result["status"]="DESKTOP_CREATE_FAILED"; return result
        os.makedirs(cfg["profile"],exist_ok=True)
        cmd=f'"{CHROME}" --remote-debugging-port={port} --remote-allow-origins=* --user-data-dir="{cfg["profile"]}" --no-first-run --no-default-browser-check {cfg["url"]}'
        si=STARTUPINFO();si.cb=ctypes.sizeof(si);si.lpDesktop=desktop;pi=PROCESS_INFORMATION();buf=ctypes.create_unicode_buffer(cmd)
        if not kernel32.CreateProcessW(None,buf,None,None,False,0,None,None,ctypes.byref(si),ctypes.byref(pi)):
            result["status"]="CHROME_LAUNCH_FAILED";return result
        pid=int(pi.dwProcessId);kernel32.CloseHandle(pi.hThread);kernel32.CloseHandle(pi.hProcess)
        endpoint=wait_cdp(port)
        if not endpoint:result["status"]="CDP_NOT_READY";return result
        with sync_playwright() as p:
            browser=p.chromium.connect_over_cdp(endpoint);ctx=browser.contexts[0];page=ctx.pages[0] if ctx.pages else ctx.new_page();deadline=time.time()+timeout;box=None
            while time.time()<deadline:
                try:
                    body=page.locator('body').inner_text(timeout=2000);low=body.lower()
                    if any(x in low for x in ['sign in','log in','login','entrar','continue with google','continuar com o google','sign up','criar conta']):
                        result["status"]="LOGIN_REQUIRED"
                    for sel in PROMPT_SELECTORS:
                        loc=page.locator(sel)
                        for i in range(loc.count()-1,-1,-1):
                            if loc.nth(i).is_visible():box=loc.nth(i);break
                        if box is not None:break
                    if box is not None:break
                except Exception:pass
                time.sleep(1)
            if box is None:
                if not result["status"]:result["status"]="NO_PROMPT_BOX"
                browser.close();return result
            try:box.fill(prompt)
            except Exception:box.click();page.keyboard.type(prompt)
            page.keyboard.press('Enter');time.sleep(4);stable='';hits=0;end=time.time()+60
            while time.time()<end:
                try:
                    response=''
                    for sel in ASSISTANT_SELECTORS:
                        loc=page.locator(sel)
                        for i in range(loc.count()-1,-1,-1):
                            txt=loc.nth(i).inner_text(timeout=1000).strip()
                            if txt and txt!=prompt:response=txt;break
                        if response:break
                    if response:
                        if response==stable:hits+=1
                        else:stable=response;hits=0
                        if hits>=2:result.update({"ok":True,"status":"SUCCESS","response":response[:8000]});break
                except Exception:pass
                time.sleep(1.5)
            if not result["status"] or result["status"]=="LOGIN_REQUIRED":
                if box is not None and not result["ok"]:result["status"]="RESPONSE_TIMEOUT"
            browser.close()
    finally:
        if pid:subprocess.run(['taskkill','/PID',str(pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if hdesk:user32.CloseDesktop(hdesk)
        result["elapsed_s"]=round(time.time()-started,2)
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--provider',choices=sorted(PROVIDERS),required=True);ap.add_argument('--prompt',required=True);args=ap.parse_args();print(json.dumps(run(args.provider,args.prompt),ensure_ascii=False))
