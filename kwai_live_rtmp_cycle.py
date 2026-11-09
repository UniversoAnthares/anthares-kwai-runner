#!/usr/bin/env python3
"""Kwai Studio RTMP six-hour renewal using existing Hostinger Cron and GitLab SSH."""
from __future__ import annotations

import base64
import io
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
from kwai_live_6h_cycle import (
    issue_and_state, save_state, room_status, call, initial_state, SIX_HOURS,
)
from kwai_live_cloud_network import extract_room_id

EXPECTED_OWNER = "Lucas Rosalem"
STUDIO = "https://studio.kwai.com"
REMOTE = "/home/u566597497/.anthares-kw12"
TIMEOUT = 32


def ssh(command: str, data: bytes | None = None, timeout: int = 40) -> str:
    host = os.environ.get("KW12_SSH_HOST", "").strip()
    user = os.environ.get("KW12_SSH_USER", "").strip()
    port = os.environ.get("KW12_SSH_PORT", "65002").strip()
    identity = os.environ.get("KW12_SSH_KEY_FILE", "").strip()
    if not (host and user and port.isdigit() and identity and Path(identity).is_file()):
        raise RuntimeError("KW12_EXISTING_SSH_BRIDGE_UNAVAILABLE")
    result = subprocess.run([
        "ssh", "-p", port, "-i", identity,
        "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
        "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10",
        f"{user}@{host}", command,
    ], input=data, capture_output=True, timeout=timeout, check=False)
    if result.returncode:
        # Deliberately omit SSH stderr: it might contain a stream destination.
        raise RuntimeError("KW12_REMOTE_HOST_COMMAND_FAILED")
    return result.stdout.decode("utf8", "replace")


def owner_authorized(page) -> bool:
    result = page.evaluate("""async()=>{try{
        const response=await fetch('/rest/o/w/live/supplier/cloudLive/checkPermission',
                                   {credentials:'include'});
        const data=await response.json();
        const user=data.userInfo||data.data?.userInfo||{};
        return {http:response.status,
                permitted:data.result===1 || !!(user.ksId||user.userId),
                identity:(document.body?.innerText||'').includes('Lucas Rosalem')};
    }catch(e){return {http:0,permitted:false,identity:false}}}""")
    return bool(result.get("http") == 200 and result.get("permitted")
                and result.get("identity"))


def cover() -> bytes:
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (720, 1280), (18, 20, 26))
    draw = ImageDraw.Draw(im)
    title = "UNIVERSO ANTHARES"
    subtitle = "LITERATURA E ESCRITA"
    draw.text((80, 550), title, fill="white")
    draw.text((110, 635), subtitle, fill="white")
    dest = io.BytesIO()
    im.save(dest, format="JPEG", quality=88)
    return dest.getvalue()


def create_rtmp_room(page) -> str:
    response = {}
    def watch(res):
        if "cloudLive/createRoom" in res.url:
            try:
                data = res.json()
                if isinstance(data, dict):
                    response.update(data)
            except (ValueError, RuntimeError):
                pass
    page.on("response", watch)
    page.goto(STUDIO + "/live/list?source=", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(1500)
    if not owner_authorized(page):
        raise RuntimeError("KW12_EXPECTED_STUDIO_OWNER_NOT_AUTHORIZED")
    page.get_by_role("button", name=re.compile(r"criar tr[aá]fego", re.I)).first.click()
    page.wait_for_timeout(500)
    mode = page.get_by_text(re.compile(
        r"transmiss[aã]o ao vivo via envio de transmiss[aã]o", re.I), exact=False)
    if not mode.count():
        raise RuntimeError("KW12_RTMP_MODE_UNAVAILABLE")
    mode.first.click()
    page.wait_for_timeout(650)
    fields = page.locator('input[type="text"]:visible')
    if not fields.count():
        raise RuntimeError("KW12_ROOM_TITLE_FIELD_MISSING")
    fields.first.fill("Universo Anthares: Livros e Escrita")
    uploader = page.locator('input[type="file"]').last
    if not uploader.count():
        raise RuntimeError("KW12_ROOM_COVER_FIELD_MISSING")
    uploader.set_input_files({
        "name": "universo-anthares-live.jpg",
        "mimeType": "image/jpeg",
        "buffer": cover(),
    })
    page.get_by_role("button", name=re.compile(r"criar tr[aá]fego", re.I)).last.click()
    deadline = time.monotonic() + 30
    while not response and time.monotonic() < deadline:
        page.wait_for_timeout(350)
    room = extract_room_id(response)
    if response.get("result") != 1 or not re.fullmatch(r"\d{10,16}", room):
        raise RuntimeError("KW12_RTMP_ROOM_CREATION_NOT_ACCEPTED")
    return room


def stream_endpoint(page, room: str) -> tuple[str, str]:
    page.goto(STUDIO + "/live/detail/" + room,
              wait_until="domcontentloaded", timeout=60000)
    for _ in range(24):
        values = page.locator("input").evaluate_all(
            "(es)=>es.map(x=>x.value||'').filter(Boolean)")
        server = next((x for x in values if
            re.fullmatch(r"rtmps?://[A-Za-z0-9.-]+:\d{2,5}/[A-Za-z0-9/_-]+", x)), "")
        key = next((x for x in values if
            re.fullmatch(r"kszt_[A-Za-z0-9_.?&%=-]+", x)), "")
        if server and key:
            if not re.fullmatch(
                r"rtmps?://(?:[A-Za-z0-9-]+\.)*(?:itotio\.com|kwai\.com):\d{2,5}/[A-Za-z0-9/_-]+",
                server):
                raise RuntimeError("KW12_RTMP_DESTINATION_REJECTED")
            return server, key
        page.wait_for_timeout(650)
    raise RuntimeError("KW12_RTMP_DESTINATION_NOT_AVAILABLE")


def activate_hostinger(room: str, server: str, key: str) -> None:
    # Existing activate-room.sh accepts three stdin lines. Never place stream
    # credentials in a command argument, GitHub Issue, log, or GitHub artifact.
    payload = f"{room}\n{server}\n{key}\n".encode("utf8")
    receipt = ssh("bash " + REMOTE + "/activate-room.sh", payload)
    if "SALA_CONFIGURADA=" + room not in receipt:
        raise RuntimeError("KW12_HOSTINGER_ACTIVATION_NOT_ACKNOWLEDGED")
    # The user's minute cron may have started the stream concurrently.
    ssh("bash " + REMOTE + "/kw12-cron-tick.sh")


def remove_hostinger_room(room: str) -> None:
    if not re.fullmatch(r"\d{10,16}", room):
        raise RuntimeError("KW12_INVALID_ROOM_ID")
    script = ("set -euo pipefail; root=" + REMOTE + "; "
              "conf=$root/active-room.env; "
              "[ -s \"$conf\" ] || exit 0; "
              "source \"$conf\"; "
              "[ \"$ROOM_ID\" = \"" + room + "\" ] || exit 0; "
              "pidfile=$root/ffmpeg-$ROOM_ID.pid; "
              "if [ -s \"$pidfile\" ]; then "
              "read -r pid < \"$pidfile\"; "
              "case \"$pid\" in *[!0-9]*|'') exit 2 ;; esac; "
              "kill \"$pid\" 2>/dev/null || true; fi; "
              "rm -f \"$pidfile\" \"$conf\" \"$root/rtmp-$ROOM_ID\"; "
              "echo KW12_OLD_ROOM_CLEARED=1")
    ssh("bash -c " + __import__("shlex").quote(script))


def wait_for_stream(room: str) -> None:
    # A stream-process acknowledgement is required before starting the LIVE.
    for _ in range(9):
        status = ssh("bash -lc " + __import__("shlex").quote(
            "p=" + REMOTE + "/ffmpeg-" + room + ".pid; "
            "progress=" + REMOTE + "/cron-rtmp-" + room + ".progress; "
            "if test -s \"$p\" && kill -0 \"$(cat \"$p\")\" 2>/dev/null "
            "&& grep -Eq '^out_time_ms=[1-9][0-9]*
            return
        time.sleep(3)
    raise RuntimeError("KW12_RTMP_PUSH_NOT_ALIVE")


def create_and_start(page, issue_id: int, state: dict) -> None:
    room = ""
    host_active = False
    live_active = False
    persisted = False
    try:
        room = create_rtmp_room(page)
        server, key = stream_endpoint(page, room)
        activate_hostinger(room, server, key)
        host_active = True
        del server, key
        wait_for_stream(room)
        result = call(page, "startLive", room)
        if (result.get("body") or {}).get("result") != 1:
            raise RuntimeError("KW12_STUDIO_LIVE_START_REJECTED")
        live_active = True
        good = 0
        for _ in range(12):
            if room_status(page, room) == 1:
                good += 1
                if good >= 2:
                    break
            page.wait_for_timeout(2500)
        if good < 2:
            raise RuntimeError("KW12_STUDIO_LIVE_NOT_CONFIRMED")
        now = int(time.time())
        updated = {"version": 1, "status": "active", "room_id": room,
                   "started_at": now, "renew_after": now + SIX_HOURS,
                   "cycle": int(state.get("cycle", 0)) + 1,
                   "hls_url": os.environ.get("ANTHARES_PUBLIC_HLS_URL", ""),
                   "mode": "rtmp_hostinger"}
        save_state(issue_id, updated)
        persisted = True
        print("KW12_RTMP_SIX_HOUR_CYCLE_ACTIVE=1", flush=True)
        print("KW12_NEXT_RENEWAL_UNIX=" + str(updated["renew_after"]), flush=True)
    finally:
        if room and not persisted:
            op = "stopLive" if live_active else "cancelLive"
            try:
                call(page, op, room)
            except Exception:
                print("KW12_NEW_ROOM_CLEANUP_INCOMPLETE=1", file=sys.stderr)
            if host_active:
                try:
                    remove_hostinger_room(room)
                except Exception:
                    print("KW12_REMOTE_HOST_CLEANUP_INCOMPLETE=1", file=sys.stderr)


def open_context(playwright):
    state = os.environ.get("KWAI_LIVE_STORAGE_STATE_B64", "").strip()
    if state:
        try:
            data = json.loads(base64.b64decode(state, validate=True))
            if not isinstance(data.get("cookies"), list):
                raise ValueError("storage state missing cookies")
        except (ValueError, TypeError) as exc:
            raise RuntimeError("KW12_CLOUD_STATE_SECRET_INVALID") from exc
        b = playwright.chromium.launch(headless=True)
        return b, b.new_context(storage_state=data, locale="pt-BR")
    directory = os.environ.get("KW12_STUDIO_PROFILE_DIR", "")
    if not directory or not Path(directory).is_dir():
        raise RuntimeError("KW12_REMOTE_STUDIO_AUTHORIZATION_REQUIRED")
    context = playwright.chromium.launch_persistent_context(
        directory, headless=True,
        args=["--no-sandbox", "--disable-dev-shm-usage"], locale="pt-BR")
    return None, context


def main() -> None:
    issue_id, state = issue_and_state()
    if state.get("status") == "active" and int(time.time()) < int(state.get("renew_after", 0)):
        print("KW12_CURRENT_ROOM_IN_SIX_HOUR_WINDOW=1", flush=True)
        return
    with sync_playwright() as pw:
        browser, ctx = open_context(pw)
        try:
            page = ctx.new_page()
            page.set_default_timeout(14000)
            page.goto(STUDIO + "/live/list?source=", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)
            if not owner_authorized(page):
                raise RuntimeError("KW12_REMOTE_STUDIO_AUTHORIZATION_REQUIRED")
            if state.get("status") == "active":
                room = str(state["room_id"])
                status = room_status(page, room)
                if status == 1:
                    reply = call(page, "stopLive", room)
                    if (reply.get("body") or {}).get("result") != 1 and room_status(page, room) == 1:
                        raise RuntimeError("KW12_PREVIOUS_ROOM_STILL_ACTIVE")
                remove_hostinger_room(room)
                state = dict(state, status="ended", ended_at=int(time.time()))
                save_state(issue_id, state)
                print("KW12_PREVIOUS_ROOM_ENDED=1", flush=True)
            create_and_start(page, issue_id, state)
        finally:
            ctx.close()
            if browser:
                browser.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("KW12_RTMP_CYCLE_ERROR=" + str(e), file=sys.stderr, flush=True)
        sys.exit(1)
