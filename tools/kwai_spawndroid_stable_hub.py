#!/usr/bin/env python3
"""One-shot SpawnDroid WebDriver Hub preflight for official Kwai APK.

This module never logs in, chooses videos, creates Neon leases or posts media.
Hobby session consumption requires two explicit environment gates. WebDriver
CI token is distinct from the SpawnDroid REST API key and is never printed.

Docs: https://docs.spawndroid.io/docs/ci-tests/
"""
from __future__ import annotations

import argparse
import hashlib
import time
import json
import os
import re
import sys
import urllib.error
import urllib.request

HUB = "https://stream.spawndroid.io/wd/hub"
API = "https://app.spawndroid.io"
KWAIPKG = "com.kwai.video"
SLUG = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{1,100}$")
SESSION = re.compile(r"^[A-Za-z0-9_-]{8,130}$")


class HubError(Exception):
    pass


class SpawnDroidHub:
    def __init__(self, token, transport=None, api_token=None, api_transport=None):
        if not str(token).strip():
            raise HubError("hub_token_missing")
        self._token = str(token).strip()
        self.transport = transport or urllib.request.urlopen
        self._api_token = str(api_token or "").strip()
        self.api_transport = api_transport or urllib.request.urlopen

    def send(self, method, route, payload=None):
        if not route.startswith("/session") or ".." in route or "://" in route:
            raise HubError("invalid_route")
        body = json.dumps(payload, separators=(",", ":")).encode() if payload is not None else None
        headers = {"Authorization": "Bearer " + self._token,
                   "Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(HUB + route, method=method,
                                     headers=headers, data=body)
        try:
            with self.transport(req, timeout=28) as resp:
                raw = resp.read(65536)
                result = json.loads(raw.decode("utf-8"))
                if not isinstance(result, dict):
                    raise HubError("invalid_response")
                if isinstance(result.get("value"), dict) and result["value"].get("error"):
                    raise HubError("webdriver_error")
                return result
        except urllib.error.HTTPError as exc:
            names = {400:"invalid_hub_request", 401:"hub_auth_failed",
                     402:"hobby_quota_exhausted",403:"scope_denied",
                     404:"session_not_found",409:"session_in_progress",
                     429:"runner_limit",502:"host_unavailable",
                     503:"hub_unavailable"}
            raise HubError(names.get(exc.code,"http_" + str(exc.code))) from None
        except urllib.error.URLError:
            raise HubError("hub_transport_error") from None
        except (UnicodeError,ValueError,TypeError):
            raise HubError("hub_invalid_json") from None

    def _api_get(self, route):
        """Read-only SpawnDroid API. The CI token alone cannot verify teardown."""
        if not self._api_token:
            raise HubError("api_readback_key_missing")
        if not route.startswith("/api/") or ".." in route or "?" in route or "://" in route:
            raise HubError("invalid_api_route")
        req = urllib.request.Request(
            API + route, method="GET",
            headers={"Authorization": "Bearer " + self._api_token,
                     "Accept": "application/json"})
        try:
            with self.api_transport(req, timeout=20) as resp:
                result = json.loads(resp.read(65536).decode("utf-8"))
                if not isinstance(result, dict):
                    raise HubError("api_response_invalid")
                return result
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise HubError("api_not_found") from None
            names = {401: "api_auth_failed", 402: "hobby_quota_exhausted",
                     403: "api_scope_denied", 429: "runner_limit",
                     502: "api_host_unavailable", 503: "api_unavailable"}
            raise HubError(names.get(exc.code, "api_http_" + str(exc.code))) from None
        except urllib.error.URLError:
            raise HubError("api_transport_error") from None
        except (ValueError, UnicodeError, TypeError):
            raise HubError("api_invalid_json") from None

    @staticmethod
    def _package(record):
        if not isinstance(record, dict):
            return ""
        package = record.get("packageName") or record.get("package")
        manifest = record.get("manifest")
        if not package and isinstance(manifest, dict):
            package = manifest.get("packageName") or manifest.get("package")
        if isinstance(package, dict):
            package = package.get("name") or package.get("package")
        return str(package or "")

    def _preflight(self, slug):
        apps = self._api_get("/api/apps").get("apps")
        profiles = self._api_get("/api/device-profiles").get("profiles")
        history = self._api_get("/api/sessions").get("sessions")
        if not all(isinstance(items, list) for items in (apps, profiles, history)):
            raise HubError("api_preflight_shape_invalid")
        matches = [a for a in apps if isinstance(a, dict) and a.get("slug") == slug]
        if len(matches) != 1 or self._package(matches[0]) != KWAIPKG:
            raise HubError("registered_official_kwai_missing")
        if not any(isinstance(p, dict) and p.get("id") == "android-14-phone"
                   for p in profiles):
            raise HubError("android14_profile_unavailable")
        terminal = {"stopped", "terminated", "ended", "completed", "finished",
                    "failed", "expired", "passed", "cancelled"}
        for item in history:
            if not isinstance(item, dict):
                raise HubError("session_history_shape_invalid")
            state = str(item.get("state") or item.get("status") or "").lower()
            if not (state in terminal or item.get("endedAt") or
                    item.get("ended_at") or item.get("stoppedAt")):
                raise HubError("workspace_sessions_conflict_or_unknown")
        return True

    def _terminal_readback(self, provider_session_id):
        """Independent terminal readback; DELETE acknowledgement alone is insufficient."""
        route = "/api/v1/sessions/" + provider_session_id
        terminal = {"stopped", "terminated", "ended", "completed",
                    "finished", "failed", "expired", "cancelled"}
        for attempt in range(5):
            try:
                detail = self._api_get(route)
            except HubError as exc:
                if str(exc) != "api_not_found":
                    raise
                detail = None
            if detail is not None:
                state = str(detail.get("state") or "").lower()
                if state in terminal:
                    return state
            # The per-run endpoint may stop serving the ended session. In that
            # case the authenticated workspace history is an independent proof.
            history = self._api_get("/api/sessions").get("sessions")
            if not isinstance(history, list):
                raise HubError("session_history_shape_invalid")
            for item in history:
                if not isinstance(item, dict):
                    continue
                if provider_session_id not in (
                    str(item.get("id") or ""), str(item.get("sessionId") or "")):
                    continue
                state = str(item.get("state") or item.get("status") or "").lower()
                if state in terminal or item.get("endedAt") or item.get("ended_at"):
                    return state or "ended_in_history"
            if attempt < 4:
                time.sleep(1)
        raise HubError("hub_teardown_state_unverified")

    def verify_kwai_once(self, slug, *, enable=False, free_hobby=False,
                         verified_slug=""):
        if not enable or not free_hobby:
            raise HubError("launch_guard_disabled")
        if not SLUG.fullmatch(str(slug or "")):
            raise HubError("invalid_artifact_slug")
        if slug != verified_slug:
            raise HubError("agent01_verified_slug_required")
        if not self._api_token:
            raise HubError("api_readback_key_missing")
        self._preflight(slug)

        request = {"capabilities": {"alwaysMatch": {
            "platformName": "Android",
            "appium:automationName": "UiAutomator2",
            "spawndroid:app": slug,
            "spawndroid:profile": "android-14-phone",
        }, "firstMatch": [{}]}}
        start = time.monotonic()
        # POST ambiguity: never retry CREATE automatically, even on timeout.
        result = self.send("POST", "/session", request)
        value = result.get("value")
        if not isinstance(value, dict):
            raise HubError("session_response_invalid_check_runs")
        session_id = str(value.get("sessionId") or result.get("sessionId") or "")
        if not SESSION.fullmatch(session_id):
            raise HubError("hub_session_id_missing_check_runs")
        caps = value.get("capabilities") or {}
        if not isinstance(caps, dict):
            caps = {}
        provider_id = str(caps.get("spawndroid:sessionId") or "")
        proof = {
            "web_driver_session_ref": hashlib.sha256(session_id.encode()).hexdigest()[:16],
            "provider_session_ref": (hashlib.sha256(provider_id.encode()).hexdigest()[:16]
                                     if provider_id else None),
            "device_serial": str(caps.get("appium:udid") or ""),
            "android_version": str(caps.get("platformVersion") or
                                   caps.get("appium:platformVersion") or ""),
            "package": str(caps.get("spawndroid:appPackage") or ""),
            "foreground_state": None,
            "ui_source_accessible": False,
            "web_driver_delete_ack": False,
            "provider_terminal_state": None,
            "publication_attempted": False,
        }
        passed = False
        try:
            if proof["package"] != KWAIPKG:
                raise HubError("installed_package_mismatch")
            if not provider_id.startswith("sess_") or not SESSION.fullmatch(provider_id):
                raise HubError("provider_session_id_missing")
            if not proof["device_serial"] or not proof["android_version"]:
                raise HubError("device_capabilities_unverified")
            self.send("POST", "/session/" + session_id + "/execute/sync", {
                "script": "mobile: activateApp", "args": [{"appId": KWAIPKG}]})
            state = self.send("POST", "/session/" + session_id + "/execute/sync", {
                "script": "mobile: queryAppState", "args": [{"appId": KWAIPKG}]})
            proof["foreground_state"] = state.get("value")
            if proof["foreground_state"] != 4:
                raise HubError("kwai_foreground_unverified")
            source = self.send("GET", "/session/" + session_id + "/source")
            proof["ui_source_accessible"] = (isinstance(source.get("value"), str) and
                                             bool(source["value"].strip()))
            if not proof["ui_source_accessible"]:
                raise HubError("ui_source_unverified")
            passed = True
        finally:
            # Always attempt teardown for the exact allocated WebDriver session.
            # Any ambiguous DELETE/readback blocks a second canary.
            try:
                deleted = self.send(
                    "DELETE", "/session/" + session_id +
                    "?result=" + ("passed" if passed else "failed"))
                if deleted.get("value") is not None:
                    raise HubError("hub_delete_response_unverified")
                proof["web_driver_delete_ack"] = True
                proof["provider_terminal_state"] = self._terminal_readback(provider_id)
            except HubError as exc:
                raise HubError("hub_teardown_unverified_reconcile_required") from exc

        proof["elapsed_seconds"] = round(time.monotonic() - start, 2)
        proof["android_session_started"] = True
        proof["kwai_app_activated_and_foreground"] = True
        proof["provider_terminal_confirmed"] = True
        return proof


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slug",default=os.getenv("SPAWNDROID_KWAI_ARTIFACT_SLUG",""))
    p.add_argument("--execute",action="store_true")
    args=p.parse_args()
    token=os.getenv("SPAWNDROID_CI_TOKEN","")
    api_token=os.getenv("SPAWNDROID_API_KEY","")
    if not token:
        print("KWAI_STABLE_HUB=TOKEN_NOT_CONFIGURED")
        return 0 if not args.execute else 20
    if not args.execute:
        print("KWAI_STABLE_HUB=CONFIGURED_NOT_STARTED")
        return 0
    try:
        client=SpawnDroidHub(token, api_token=api_token)
        proof=client.verify_kwai_once(
            args.slug,
            enable=os.getenv("SPAWNDROID_HUB_CANARY_ENABLED")=="1",
            free_hobby=os.getenv("SPAWNDROID_HOBBY_FREE_CONFIRMED")=="1",
            verified_slug=os.getenv("SPAWNDROID_KWAI_VERIFIED_SLUG", ""))
        print("KWAI_STABLE_HUB=APP_FOREGROUND_AND_TERMINAL_READBACK")
        print("KWAI_STABLE_HUB_PROOF="+json.dumps(proof, sort_keys=True))
        print("KWAI_PUBLICATION_ATTEMPTED=0")
        return 0
    except HubError as exc:
        print("KWAI_STABLE_HUB="+str(exc))
        print("KWAI_PUBLICATION_ATTEMPTED=0")
        return 21


if __name__=="__main__":
    sys.exit(main())
