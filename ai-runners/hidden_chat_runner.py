#!/usr/bin/env python3
"""Hidden-desktop web chat runner for dedicated non-Claude provider profiles.

The runner launches installed Chrome headful on a separate Win32 desktop, attaches
through CDP/Playwright and kills only the isolated process tree. It never touches
the user's normal Chrome profile.

For deterministic integration use --expect plus --expect-end. The prompt should
contain each marker once as formatting instructions. Success requires both markers
to appear again in page text and a non-empty response between a valid marker pair.
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import json
import os
import socket
import subprocess
import time
import uuid
import urllib.request

from playwright.sync_api import sync_playwright

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = r"C:\Users\Lucas\AntharesWork"
PROVIDERS = {
    "grok": {"url": "https://grok.com/", "profile": os.path.join(BASE, "grok-hidden-desktop-profile")},
    "manus": {"url": "https://manus.im/", "profile": os.path.join(BASE, "manus-hidden-desktop-profile")},
    "perplexity": {"url": "https://www.perplexity.ai/", "profile": os.path.join(BASE, "perplexity-hidden-desktop-profile")},
    "gemini": {"url": "https://gemini.google.com/app", "profile": os.path.join(BASE, "gemini-hidden-desktop-profile")},
}
PROMPT_SELECTORS = ["textarea", "div[contenteditable='true']", "[role='textbox']"]
ASSISTANT_SELECTORS = [
    '[data-testid*="assistant"]', '[data-testid*="answer"]',
    '[class*="assistant"]', '[class*="answer"]', 'main article', 'article'
]
LOGIN_TERMS = [
    "sign in", "log in", "login", "entrar", "continue with google",
    "continuar com o google", "sign up", "criar conta"
]

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32 = ctypes.WinDLL("user32", use_last_error=True)


class STARTUPINFO(ctypes.Structure):
    _fields_ = [
        ("cb", wt.DWORD), ("lpReserved", wt.LPWSTR), ("lpDesktop", wt.LPWSTR),
        ("lpTitle", wt.LPWSTR), ("dwX", wt.DWORD), ("dwY", wt.DWORD),
        ("dwXSize", wt.DWORD), ("dwYSize", wt.DWORD), ("dwXCountChars", wt.DWORD),
        ("dwYCountChars", wt.DWORD), ("dwFillAttribute", wt.DWORD), ("dwFlags", wt.DWORD),
        ("wShowWindow", wt.WORD), ("cbReserved2", wt.WORD),
        ("lpReserved2", ctypes.POINTER(ctypes.c_byte)), ("hStdInput", wt.HANDLE),
        ("hStdOutput", wt.HANDLE), ("hStdError", wt.HANDLE),
    ]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wt.HANDLE), ("hThread", wt.HANDLE),
        ("dwProcessId", wt.DWORD), ("dwThreadId", wt.DWORD),
    ]


user32.CreateDesktopW.argtypes = [wt.LPCWSTR, wt.LPCWSTR, ctypes.c_void_p, wt.DWORD, wt.DWORD, ctypes.c_void_p]
user32.CreateDesktopW.restype = wt.HANDLE
kernel32.CreateProcessW.argtypes = [
    wt.LPCWSTR, wt.LPWSTR, ctypes.c_void_p, ctypes.c_void_p, wt.BOOL, wt.DWORD,
    ctypes.c_void_p, wt.LPCWSTR, ctypes.POINTER(STARTUPINFO), ctypes.POINTER(PROCESS_INFORMATION)
]
kernel32.CreateProcessW.restype = wt.BOOL


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_cdp(port, seconds=30):
    end = time.time() + seconds
    while time.time() < end:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1) as r:
                if r.status == 200:
                    return f"http://127.0.0.1:{port}"
        except Exception:
            time.sleep(0.5)
    return None


def find_box(page):
    for selector in PROMPT_SELECTORS:
        try:
            loc = page.locator(selector)
            for i in range(loc.count() - 1, -1, -1):
                try:
                    if loc.nth(i).is_visible():
                        return loc.nth(i)
                except Exception:
                    pass
        except Exception:
            pass
    return None


def extract_between_markers(text, start_marker, end_marker):
    if not start_marker or not end_marker:
        return ""
    candidates = []
    pos = 0
    while True:
        start = text.find(start_marker, pos)
        if start < 0:
            break
        content_start = start + len(start_marker)
        end = text.find(end_marker, content_start)
        if end < 0:
            break
        chunk = text[content_start:end].strip()
        chunk = chunk.replace(start_marker, "").replace(end_marker, "").strip()
        if chunk and chunk != "[sua resposta]":
            candidates.append(chunk)
        pos = content_start
    return candidates[-1] if candidates else ""


def extract_assistant_text(page, prompt):
    for selector in ASSISTANT_SELECTORS:
        try:
            loc = page.locator(selector)
            for i in range(loc.count() - 1, -1, -1):
                txt = loc.nth(i).inner_text(timeout=1000).strip()
                if txt and txt != prompt and len(txt) > 1:
                    return txt
        except Exception:
            pass
    try:
        body = page.locator("body").inner_text(timeout=1500)
        idx = body.rfind(prompt)
        if idx >= 0:
            return body[idx + len(prompt):].strip()[:8000]
    except Exception:
        pass
    return ""


def run(provider, prompt, timeout=90, expect=None, expect_end=None, response_timeout=60):
    cfg = PROVIDERS[provider]
    started = time.time()
    port = free_port()
    desktop = "AntharesChat_" + provider + "_" + uuid.uuid4().hex[:8]
    hdesk = user32.CreateDesktopW(desktop, None, None, 0, 0x10000000, None)
    pid = None
    result = {
        "provider": provider, "ok": False, "status": None, "response": "",
        "elapsed_s": None, "expected": expect, "expected_end": expect_end,
    }
    try:
        if not hdesk:
            result["status"] = "DESKTOP_CREATE_FAILED"
            return result
        os.makedirs(cfg["profile"], exist_ok=True)
        cmd = (
            f'"{CHROME}" --remote-debugging-port={port} --remote-allow-origins=* '
            f'--user-data-dir="{cfg["profile"]}" --no-first-run --no-default-browser-check {cfg["url"]}'
        )
        si = STARTUPINFO(); si.cb = ctypes.sizeof(si); si.lpDesktop = desktop
        pi = PROCESS_INFORMATION(); buf = ctypes.create_unicode_buffer(cmd)
        if not kernel32.CreateProcessW(None, buf, None, None, False, 0, None, None, ctypes.byref(si), ctypes.byref(pi)):
            result["status"] = "CHROME_LAUNCH_FAILED"
            return result
        pid = int(pi.dwProcessId)
        kernel32.CloseHandle(pi.hThread); kernel32.CloseHandle(pi.hProcess)
        endpoint = wait_cdp(port)
        if not endpoint:
            result["status"] = "CDP_NOT_READY"
            return result

        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(endpoint)
            ctx = browser.contexts[0]
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            deadline = time.time() + timeout
            box = None
            while time.time() < deadline:
                try:
                    body = page.locator("body").inner_text(timeout=2000)
                    low = body.lower()
                    result["login_required"] = any(term in low for term in LOGIN_TERMS)
                    box = find_box(page)
                    if box is not None:
                        break
                except Exception:
                    pass
                time.sleep(1)
            if box is None:
                result["status"] = "LOGIN_REQUIRED" if result.get("login_required") else "NO_PROMPT_BOX"
                browser.close()
                return result

            try:
                box.fill(prompt)
            except Exception:
                box.click(); page.keyboard.type(prompt)
            page.keyboard.press("Enter")
            time.sleep(2)
            end_time = time.time() + response_timeout

            if expect:
                start_count = end_count = 0
                while time.time() < end_time:
                    try:
                        body = page.locator("body").inner_text(timeout=2000)
                        start_count = body.count(expect)
                        end_count = body.count(expect_end) if expect_end else 0
                        start_ok = start_count >= 2
                        end_ok = (not expect_end) or end_count >= 2
                        if start_ok and end_ok:
                            response = extract_between_markers(body, expect, expect_end) if expect_end else extract_assistant_text(page, prompt)
                            if expect_end and not response:
                                time.sleep(1.25)
                                continue
                            result.update({
                                "ok": True, "status": "SUCCESS", "response": response,
                                "marker_count": start_count, "end_marker_count": end_count,
                                "url": page.url, "title": page.title(),
                            })
                            break
                    except Exception:
                        pass
                    time.sleep(1.25)
                if not result["ok"]:
                    result.update({
                        "status": "MARKER_TIMEOUT", "marker_count": start_count,
                        "end_marker_count": end_count, "url": page.url, "title": page.title(),
                    })
            else:
                stable = ""; hits = 0
                while time.time() < end_time:
                    try:
                        response = extract_assistant_text(page, prompt)
                        if response:
                            if response == stable:
                                hits += 1
                            else:
                                stable = response; hits = 0
                            if hits >= 2:
                                result.update({
                                    "ok": True, "status": "SUCCESS", "response": response[:8000],
                                    "url": page.url, "title": page.title(),
                                })
                                break
                    except Exception:
                        pass
                    time.sleep(1.5)
                if not result["ok"]:
                    result.update({"status": "RESPONSE_TIMEOUT", "url": page.url, "title": page.title()})
            browser.close()
    finally:
        if pid:
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if hdesk:
            user32.CloseDesktop(hdesk)
        result["elapsed_s"] = round(time.time() - started, 2)
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=sorted(PROVIDERS), required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--expect")
    ap.add_argument("--expect-end")
    ap.add_argument("--timeout", type=int, default=90)
    ap.add_argument("--response-timeout", type=int, default=60)
    args = ap.parse_args()
    print(json.dumps(
        run(args.provider, args.prompt, args.timeout, args.expect, args.expect_end, args.response_timeout),
        ensure_ascii=False,
    ))
