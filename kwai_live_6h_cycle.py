#!/usr/bin/env python3
"""One six-hour Kwai Studio network-pull cycle, using the existing HLS origin.

Each invocation is finite: Kwai's own cloud server pulls the HLS between invocations.
The same GitHub issue is the cross-invocation state/lease record. Never start a
replacement until the previous room has run >= six hours and has stopped.
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from io import BytesIO

from playwright.sync_api import sync_playwright
from kwai_live_cloud_network import (
    HLS_URL, hls_preflight, login_if_needed, extract_room_id,
)

TITLE = "[KWAI-LIVE-6H-STATE]"
SIX_HOURS = 21600
REPO = os.environ.get("GITHUB_REPOSITORY", "UniversoAnthares/anthares-kwai-runner")
GH_TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
STORAGE_B64 = os.environ.get("KWAI_LIVE_STORAGE_STATE_B64", "").strip()


def gh(method: str, endpoint: str, payload=None):
    if not GH_TOKEN:
        raise RuntimeError("GITHUB_TOKEN_MISSING")
    url = "https://api.github.com" + endpoint
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=body, method=method, headers={
        "Authorization": "Bearer " + GH_TOKEN,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Anthares-Kwai-Live-Cycle/1.0",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)


def initial_state():
    return {"version": 1, "status": "idle", "room_id": None,
            "started_at": 0, "renew_after": 0, "hls_url": HLS_URL, "cycle": 0}


def issue_and_state():
    # The workflow concurrency group serializes all writers.
    matching = []
    page = 1
    while page <= 10:
        rows = gh("GET", "/repos/" + REPO + "/issues?state=open&per_page=100&page=" + str(page))
        matching += [row for row in rows if row.get("title") == TITLE
                     and "pull_request" not in row]
        if len(rows) < 100:
            break
        page += 1
    if page > 10 and len(rows) == 100:
        raise RuntimeError("LIVE_ISSUE_SEARCH_INCOMPLETE")
    if len(matching) > 1:
        raise RuntimeError("LIVE_MULTIPLE_STATE_ISSUES")
    if matching:
        issue = matching[0]
        state = json.loads(issue.get("body") or "{}")
        if state.get("version") != 1:
            raise RuntimeError("LIVE_STATE_SCHEMA_UNKNOWN")
        return issue["number"], state
    state = initial_state()
    issue = gh("POST", "/repos/" + REPO + "/issues", {
        "title": TITLE, "body": json.dumps(state, separators=(",", ":")),
    })
    return issue["number"], state


def save_state(issue_id, state):
    state["version"] = 1
    gh("PATCH", "/repos/" + REPO + "/issues/" + str(issue_id), {
        "body": json.dumps(state, separators=(",", ":")),
    })


def studio_context(browser):
    if STORAGE_B64:
        try:
            state = json.loads(base64.b64decode(STORAGE_B64, validate=True))
            if not isinstance(state, dict) or not isinstance(state.get("cookies"), list):
                raise ValueError("bad state")
        except Exception as e:
            raise RuntimeError("KWAI_LIVE_STATE_SECRET_INVALID") from e
        return browser.new_context(storage_state=state, viewport={"width": 1440, "height": 1000}, locale="pt-BR")
    return browser.new_context(viewport={"width": 1440, "height": 1000}, locale="pt-BR")


def call(page, endpoint, room_id):
    url = "/rest/o/w/live/supplier/cloudLive/" + endpoint
    if endpoint == "room":
        url += "?liveRoomId=" + urllib.parse.quote(room_id, safe="")
    post = endpoint in {"startLive", "stopLive", "cancelLive"}
    return page.evaluate("""async a => {
      const r = await fetch(a.url, a.post
        ? {method:'POST', headers:{'Content-Type':'application/json;charset=UTF-8'},
           body:JSON.stringify({liveRoomId:a.room})} : {});
      return {http:r.status, body:await r.json()};
    }""", {"url": url, "post": post, "room": room_id})


def room_status(page, room_id):
    result = call(page, "room", room_id)
    if result.get("http") != 200:
        raise RuntimeError("KWAI_ROOM_STATUS_HTTP_FAILED")
    obj = result.get("body") or {}
    status = (obj.get("curRoomVo") or {}).get("roomStatus")
    # An absent/malformed status is not evidence that a live has ended.
    if isinstance(status, bool) or not re.fullmatch(r"[0-9]{1,2}", str(status)):
        raise RuntimeError("KWAI_ROOM_REMOTE_STATUS_UNCONFIRMED")
    return int(status)


def stop_previous(page, issue_id, state):
    room = state.get("room_id")
    if not room or state.get("status") != "active":
        raise RuntimeError("KWAI_PREVIOUS_ROOM_STATE_INVALID")
    if time.time() < float(state["renew_after"]):
        print("KWAI_LIVE_ALREADY_RUNNING=1", flush=True)
        return False
    remote_status = room_status(page, room)
    if remote_status == 1:
        response = call(page, "stopLive", room)
        if (response.get("body") or {}).get("result") != 1:
            if room_status(page, room) == 1:
                raise RuntimeError("KWAI_PREVIOUS_ROOM_STOP_UNCONFIRMED")
    state = dict(state, status="ended", ended_at=int(time.time()))
    save_state(issue_id, state)
    print("KWAI_PREVIOUS_ROOM_ENDED=1", flush=True)
    return True


def make_cover():
    from PIL import Image, ImageDraw
    out = BytesIO()
    picture = Image.new("RGB", (720, 1280), (22, 28, 39))
    draw = ImageDraw.Draw(picture)
    draw.text((85, 590), "UNIVERSO ANTHARES", fill=(255, 255, 255))
    draw.text((85, 640), "Literatura e escrita", fill=(255, 255, 255))
    picture.save(out, format="JPEG", quality=85)
    return out.getvalue()


def create_room(page):
    created = {}
    def observe(response):
        if "cloudLive/createRoom" in response.url:
            try:
                created.update(response.json())
            except Exception:
                pass
    page.on("response", observe)
    page.get_by_role("button", name=re.compile(r"criar tr[aá]fego|create traffic", re.I)).first.click()
    page.wait_for_timeout(1200)
    card = page.get_by_text(re.compile(
        r"transmiss[aã]o ao vivo via transmiss[aã]o de rede|network", re.I), exact=False)
    if not card.count():
        raise RuntimeError("KWAI_NETWORK_PULL_OPTION_MISSING")
    card.first.click()
    page.wait_for_timeout(1000)
    fields = page.locator('input[type="text"]:visible')
    if fields.count() < 2:
        raise RuntimeError("KWAI_NETWORK_PULL_FIELDS_MISSING")
    fields.nth(0).fill(HLS_URL)
    fields.nth(1).fill("Universo Anthares — literatura e escrita")
    try:
        page.locator('input[type="file"][name="cover"]').set_input_files({
            "name": "anthares-live-cover.jpg",
            "mimeType": "image/jpeg",
            "buffer": make_cover(),
        })
    except Exception:
        raise RuntimeError("KWAI_COVER_UPLOAD_UNAVAILABLE")
    page.get_by_role("button", name=re.compile(r"criar tr[aá]fego|create traffic", re.I)).last.click()
    end = time.monotonic() + 25
    while time.monotonic() < end and not created:
        page.wait_for_timeout(250)
    room = extract_room_id(created)
    if created.get("result") != 1 or not room:
        raise RuntimeError("KWAI_ROOM_CREATION_UNCONFIRMED")
    return room


def begin_new(page, issue_id, state):
    room = ""
    activated = False
    stored = False
    try:
        room = create_room(page)
        result = call(page, "startLive", room)
        if (result.get("body") or {}).get("result") != 1:
            raise RuntimeError("KWAI_LIVE_START_REJECTED")
        activated = True
        good = 0
        end = time.monotonic() + 45
        while time.monotonic() < end:
            if room_status(page, room) == 1:
                good += 1
                if good >= 2:
                    break
            page.wait_for_timeout(4000)
        if good < 2:
            raise RuntimeError("KWAI_LIVE_START_NOT_STABLE")
        now = int(time.time())
        next_state = {
            "version": 1, "status": "active", "room_id": room,
            "started_at": now, "renew_after": now + SIX_HOURS,
            "cycle": int(state.get("cycle", 0)) + 1,
            "hls_url": HLS_URL,
        }
        save_state(issue_id, next_state)
        stored = True
        print("KWAI_LIVE_6H_CYCLE_STARTED=1", flush=True)
        print("KWAI_LIVE_CYCLE_NUMBER=" + str(next_state["cycle"]), flush=True)
        print("KWAI_LIVE_RENEW_AFTER_UTC=" + str(next_state["renew_after"]), flush=True)
    finally:
        if room and not stored:
            action = "stopLive" if activated else "cancelLive"
            try:
                result = call(page, action, room)
                if (result.get("body") or {}).get("result") != 1:
                    print("KWAI_LIVE_CLEANUP_UNCONFIRMED=1", file=sys.stderr, flush=True)
            except Exception:
                print("KWAI_LIVE_CLEANUP_UNCONFIRMED=1", file=sys.stderr, flush=True)


def main():
    # The lock in kwai-live-6h.yml must remain serial and never cancel in progress.
    issue_id, state = issue_and_state()
    # The issue describes what we last observed. An active issue alone cannot
    # prove that Kwai has kept the remote transmission open for six hours.
    hls_preflight()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=[
            "--no-sandbox", "--disable-dev-shm-usage",
        ])
        try:
            context = studio_context(browser)
            try:
                page = context.new_page()
                page.set_default_timeout(18000)
                page.goto("https://studio.kwai.com/", wait_until="domcontentloaded", timeout=90000)
                page.wait_for_timeout(3500)
                try:
                    perm = login_if_needed(page)
                except RuntimeError:
                    # Diagnostic categories only; never output form values, account IDs,
                    # credentials, cookies, QR payloads or full page markup.
                    ui = page.evaluate("""() => {
                      const t = (document.body?.innerText || '').toLowerCase();
                      const visible = e => !!e.getClientRects().length;
                      return {
                        page_path: location.pathname,
                        input_types: [...document.querySelectorAll('input')].filter(visible).map(e=>e.type),
                        iframe_count: document.querySelectorAll('iframe').length,
                        form_count: document.querySelectorAll('form').length,
                        labels: ['email','phone','password','qr code','senha','telefone','verificação','verification',
                                 'google','entrar','login','continue','continuar'].filter(x=>t.includes(x))
                      };
                    }""")
                    print("KWAI_STUDIO_LOGIN_SURFACE=" + json.dumps(ui, ensure_ascii=True), flush=True)
                    raise
                body = perm.get("body") or {}
                user = body.get("userInfo") or (body.get("data") or {}).get("userInfo") or {}
                if not (user.get("ksId") or user.get("userId")):
                    raise RuntimeError("KWAI_STUDIO_ACCOUNT_ID_UNCONFIRMED")
                if state.get("status") == "active":
                    room = str(state.get("room_id") or "")
                    if not re.fullmatch(r"[0-9]{10,21}", room):
                        raise RuntimeError("KWAI_PREVIOUS_ROOM_ID_INVALID")
                    observed = room_status(page, room)
                    if time.time() < float(state.get("renew_after", 0)):
                        if observed == 1:
                            print("KWAI_LIVE_ALREADY_RUNNING=1 remote_status=1", flush=True)
                            return
                        # A room created by a preceding run may expire early,
                        # including when the ingest stops. Rotate immediately
                        # only after the official Studio API proves it is dead.
                        state = dict(state, status="ended",
                                     ended_at=int(time.time()),
                                     end_reason="remote_room_ended_early",
                                     last_remote_status=observed)
                        save_state(issue_id, state)
                        print("KWAI_LIVE_INTERRUPTED_ROOM_RECOVERY=1", flush=True)
                    else:
                        stop_previous(page, issue_id, state)
                        state = dict(state, status="ended")
                begin_new(page, issue_id, state)
            finally:
                context.close()
        finally:
            browser.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("KWAI_LIVE_6H_ERROR=" + str(e), file=sys.stderr, flush=True)
        raise
