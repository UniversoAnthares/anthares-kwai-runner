#!/usr/bin/env python3
"""Reusable Claude web runner using a dedicated Chrome profile on a hidden Windows desktop.

The runner never reuses the user's normal Chrome profile. It launches a headful Chrome
inside a separate Win32 desktop, attaches through CDP with Playwright, sends one prompt,
returns structured JSON, and kills only the isolated Chrome process tree.
"""

import argparse
import ctypes
import ctypes.wintypes as wt
import json
import os
import socket
import subprocess
import sys
import time
import uuid
import urllib.request

from playwright.sync_api import sync_playwright

DEFAULT_PROFILE = r"C:\Users\Lucas\AntharesWork\claude-hidden-desktop-profile"
DEFAULT_CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CLAUDE_URL = "https://claude.ai/new"
PROMPT_SELECTORS = ["textarea", "div[contenteditable='true']"]
ASSISTANT_SELECTORS = [
    '[data-testid="assistant-message"]',
    '[data-testid*="assistant"]',
    'div.font-claude-response',
    'div[class*="font-claude-response"]',
    'div[class*="font-claude-message"]',
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
    _fields_ = [("hProcess", wt.HANDLE), ("hThread", wt.HANDLE),
                ("dwProcessId", wt.DWORD), ("dwThreadId", wt.DWORD)]


user32.CreateDesktopW.argtypes = [wt.LPCWSTR, wt.LPCWSTR, ctypes.c_void_p, wt.DWORD, wt.DWORD, ctypes.c_void_p]
user32.CreateDesktopW.restype = wt.HANDLE
kernel32.CreateProcessW.argtypes = [wt.LPCWSTR, wt.LPWSTR, ctypes.c_void_p, ctypes.c_void_p,
                                    wt.BOOL, wt.DWORD, ctypes.c_void_p, wt.LPCWSTR,
                                    ctypes.POINTER(STARTUPINFO), ctypes.POINTER(PROCESS_INFORMATION)]
kernel32.CreateProcessW.restype = wt.BOOL


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_cdp(port, timeout=30):
    deadline = time.time() + timeout
    url = f"http://127.0.0.1:{port}/json/version"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                if r.status == 200:
                    return f"http://127.0.0.1:{port}"
        except Exception:
            time.sleep(0.5)
    return None


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
            tail = body[idx + len(prompt):].strip()
            if tail:
                return tail[:6000]
    except Exception:
        pass
    return ""


def run_once(prompt, profile, chrome, timeout=75, response_timeout=60, expect=None):
    started = time.time()
    desktop_name = "AntharesClaude_" + uuid.uuid4().hex[:10]
    port = free_port()
    hdesk = user32.CreateDesktopW(desktop_name, None, None, 0, 0x10000000, None)
    if not hdesk:
        return {"ok": False, "status": "DESKTOP_CREATE_FAILED", "elapsed_s": round(time.time()-started, 2)}

    os.makedirs(profile, exist_ok=True)
    cmd = f'"{chrome}" --remote-debugging-port={port} --remote-allow-origins=* --user-data-dir="{profile}" --no-first-run --no-default-browser-check {CLAUDE_URL}'
    si = STARTUPINFO(); si.cb = ctypes.sizeof(si); si.lpDesktop = desktop_name
    pi = PROCESS_INFORMATION(); buf = ctypes.create_unicode_buffer(cmd)
    pid = None
    result = {"ok": False, "status": None, "response": "", "pid": None, "elapsed_s": None}

    try:
        if not kernel32.CreateProcessW(None, buf, None, None, False, 0, None, None, ctypes.byref(si), ctypes.byref(pi)):
            result["status"] = "CHROME_LAUNCH_FAILED"
            return result
        pid = int(pi.dwProcessId); result["pid"] = pid
        kernel32.CloseHandle(pi.hThread); kernel32.CloseHandle(pi.hProcess)

        endpoint = wait_cdp(port, min(timeout, 30))
        if not endpoint:
            result["status"] = "CDP_NOT_READY"
            return result

        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(endpoint)
            ctx = browser.contexts[0]
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            deadline = time.time() + timeout
            box = None
            while time.time() < deadline:
                try:
                    title = page.title()
                    body = page.locator("body").inner_text(timeout=1500)
                    low = (title + "\n" + body).lower()
                    if "um momento" in low or "just a moment" in low:
                        result["status"] = "CLOUDFLARE_CHALLENGE"
                    if any(x in low for x in ["continuar com o google", "continue with google", "sign in", "continue with email"]):
                        result["status"] = "LOGIN_REQUIRED"
                        break
                    for selector in PROMPT_SELECTORS:
                        loc = page.locator(selector)
                        for i in range(loc.count() - 1, -1, -1):
                            cand = loc.nth(i)
                            if cand.is_visible():
                                box = cand; break
                        if box is not None:
                            break
                    if box is not None:
                        break
                except Exception:
                    pass
                time.sleep(1)

            if box is None:
                if not result["status"]:
                    result["status"] = "NO_PROMPT_BOX"
                browser.close()
                return result

            try:
                box.fill(prompt)
            except Exception:
                box.click(); page.keyboard.type(prompt)
            page.keyboard.press("Enter")

            stable = None; stable_hits = 0
            rdeadline = time.time() + response_timeout
            while time.time() < rdeadline:
                time.sleep(1.5)
                try:
                    body = page.locator("body").inner_text(timeout=2000)
                    response = extract_assistant_text(page, prompt)
                    if expect and expect in body:
                        result.update({"ok": True, "status": "SUCCESS", "response": response or expect})
                        break
                    if response:
                        snapshot = response.strip()
                        if snapshot == stable:
                            stable_hits += 1
                        else:
                            stable, stable_hits = snapshot, 0
                        if stable_hits >= 2 and len(snapshot) >= 2:
                            result.update({"ok": True, "status": "SUCCESS", "response": snapshot})
                            break
                except Exception:
                    pass
            if not result["status"] or result["status"] in ("CLOUDFLARE_CHALLENGE",):
                result["status"] = "RESPONSE_TIMEOUT"
            browser.close()
    finally:
        if pid:
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        user32.CloseDesktop(hdesk)
        result["elapsed_s"] = round(time.time() - started, 2)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt")
    ap.add_argument("--prompt-file")
    ap.add_argument("--expect")
    ap.add_argument("--profile", default=DEFAULT_PROFILE)
    ap.add_argument("--chrome", default=DEFAULT_CHROME)
    ap.add_argument("--timeout", type=int, default=75)
    ap.add_argument("--response-timeout", type=int, default=60)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        cases = [
            ("Calcule 73 vezes 19. Responda apenas com o número.", "1387"),
            ("Converta a palavra ANTHARES para letras minúsculas. Responda apenas com o resultado.", "anthares"),
            ("Qual é a capital de Mato Grosso do Sul? Responda apenas com o nome da cidade.", "Campo Grande"),
        ]
        results = []
        for prompt, expect in cases:
            r = run_once(prompt, args.profile, args.chrome, args.timeout, args.response_timeout, expect)
            r["expected"] = expect
            results.append(r)
            if not r["ok"]:
                break
        print(json.dumps({"ok": len(results) == 3 and all(x["ok"] for x in results), "results": results}, ensure_ascii=False))
        return

    prompt = args.prompt
    if args.prompt_file:
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read().strip()
    if not prompt:
        ap.error("use --prompt, --prompt-file, or --self-test")
    print(json.dumps(run_once(prompt, args.profile, args.chrome, args.timeout, args.response_timeout, args.expect), ensure_ascii=False))


if __name__ == "__main__":
    main()
