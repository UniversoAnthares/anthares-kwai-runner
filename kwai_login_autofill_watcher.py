#!/usr/bin/env python3
import os, re, subprocess, time, xml.etree.ElementTree as ET

LOGIN = os.environ.get("KWAI_LOGIN", "")
PASSWORD = os.environ.get("KWAI_PASSWORD", "")
STATUS = "kwai-remote-status.txt"


def adb(*args, timeout=10, check=False):
    p = subprocess.run(["adb", *args], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=timeout)
    if check and p.returncode:
        raise RuntimeError("adb failed")
    return p.stdout


def dump_nodes():
    adb("shell", "uiautomator", "dump", "/sdcard/kwai-autofill.xml", timeout=15, check=True)
    raw = adb("exec-out", "cat", "/sdcard/kwai-autofill.xml", timeout=5, check=True)
    return list(ET.fromstring(raw).iter("node"))


def label(n):
    return " ".join((n.get("text", ""), n.get("content-desc", ""), n.get("resource-id", ""), n.get("hint", ""))).strip().lower()


def center(n):
    m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", n.get("bounds", ""))
    if not m:
        return None
    a, b, c, d = map(int, m.groups())
    return ((a + c) // 2, (b + d) // 2)


def tap(n):
    c = center(n)
    if not c:
        return False
    adb("shell", "input", "tap", str(c[0]), str(c[1]), timeout=5, check=True)
    return True


def put_secret(value):
    if not value or any(ord(ch) < 33 or ord(ch) > 126 for ch in value):
        return False
    adb("shell", "input", "text", value.replace("%", "%25"), timeout=8, check=True)
    return True


def status_contains(text):
    try:
        return text in open(STATUS, "r", encoding="utf-8", errors="ignore").read()
    except OSError:
        return False


def find_button(nodes, words):
    candidates = []
    for n in nodes:
        s = label(n)
        if any(re.search(w, s, re.I) for w in words):
            c = center(n)
            if c:
                candidates.append((n, c[1]))
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0] if candidates else None


def auth_ok():
    p = subprocess.run(["python3", "kwai_auth_probe.py"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=20)
    return p.returncode == 0 and "KWAI_AUTH_STATE=AUTHENTICATED_UI" in p.stdout


if not LOGIN or not PASSWORD:
    print("KWAI_AUTOFILL_WATCHER_SECRETS_MISSING", flush=True)
    raise SystemExit(0)

# The main login script handles onboarding and the identifier first. Wait until it
# declares the owner-interaction surface stable, then take over credential progression.
deadline = time.time() + 420
while time.time() < deadline and not status_contains("KWAI_OWNER_INTERACTION_READY"):
    time.sleep(1)
if time.time() >= deadline:
    print("KWAI_AUTOFILL_WATCHER_LOGIN_SURFACE_TIMEOUT", flush=True)
    raise SystemExit(0)

print("KWAI_AUTOFILL_WATCHER_READY", flush=True)
time.sleep(2)
identifier_advanced = False
password_submitted = False
end = time.time() + 180
while time.time() < end:
    try:
        nodes = dump_nodes()
    except Exception:
        time.sleep(2)
        continue
    page = " ".join(label(n) for n in nodes)
    if re.search(r"please check your internet connection|check your internet|verifique sua conex[aã]o|sem conex[aã]o", page, re.I):
        open("/tmp/kwai-auth-network-error-detected", "w").write("1")
        print("KWAI_POST_PASSWORD_NETWORK_ERROR_DETECTED", flush=True)
        raise SystemExit(0)
    if auth_ok():
        open("/tmp/anthares-android-done", "w").write("1")
        print("KWAI_AUTOFILL_AUTHENTICATED_SIGNALLED", flush=True)
        raise SystemExit(0)

    fields = [n for n in nodes if n.get("class", "").endswith("EditText")]
    password_fields = [n for n in fields if n.get("password") == "true" or re.search(r"password|senha", label(n), re.I)]
    if password_fields and not password_submitted:
        if tap(password_fields[0]) and put_secret(PASSWORD):
            print("KWAI_AUTOFILL_PASSWORD_FILLED", flush=True)
            time.sleep(1)
            nodes = dump_nodes()
            b = find_button(nodes, [r"^log.?in$", r"^sign.?in$", r"^entrar$", r"^continue$", r"^continuar$", r"^next$", r"^pr[oó]ximo$"])
            if b and tap(b):
                password_submitted = True
                print("KWAI_AUTOFILL_PASSWORD_SUBMITTED", flush=True)
                time.sleep(4)
                continue
    if not password_fields and not identifier_advanced:
        # Identifier is already filled by the main script. Advance to password.
        b = find_button(nodes, [r"^continue$", r"^continuar$", r"^next$", r"^pr[oó]ximo$"])
        if b and tap(b):
            identifier_advanced = True
            print("KWAI_AUTOFILL_IDENTIFIER_ADVANCED", flush=True)
            time.sleep(3)
            continue
    time.sleep(2)

print("KWAI_AUTOFILL_WATCHER_TIMEOUT", flush=True)
