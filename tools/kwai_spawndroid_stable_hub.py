#!/usr/bin/env python3
"""One-shot SpawnDroid WebDriver Hub preflight for official Kwai APK.

This module never logs in, chooses videos, creates Neon leases or posts media.
Hobby session consumption requires two explicit environment gates. WebDriver
CI token is distinct from the SpawnDroid REST API key and is never printed.

Docs: https://docs.spawndroid.io/docs/ci-tests/
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

HUB = "https://stream.spawndroid.io/wd/hub"
KWAIPKG = "com.kwai.video"
SLUG = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{1,100}$")
SESSION = re.compile(r"^[A-Za-z0-9_-]{8,130}$")


class HubError(Exception):
    pass


class SpawnDroidHub:
    def __init__(self, token, transport=None):
        if not str(token).strip():
            raise HubError("hub_token_missing")
        self._token = str(token).strip()
        self.transport = transport or urllib.request.urlopen

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
                raw = resp.read(1048576)
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

    def verify_kwai_once(self, slug, *, enable=False, free_hobby=False):
        if not enable or not free_hobby:
            raise HubError("launch_guard_disabled")
        if not SLUG.fullmatch(str(slug or "")):
            raise HubError("invalid_artifact_slug")

        # Stable Hub owns the actual Android allocation and installation.
        request = {"capabilities": {"alwaysMatch": {
            "platformName": "Android",
            "appium:automationName": "UiAutomator2",
            "spawndroid:app": slug,
            "spawndroid:profile": "android-14-phone",
        }, "firstMatch": [{}]}}
        # POST timeout or lost response is ambiguous. Never issue another
        # session creation automatically; inspect SpawnDroid Runs in the UI.
        result = self.send("POST", "/session", request)
        value = result.get("value")
        if not isinstance(value,dict):
            raise HubError("session_response_invalid")
        session_id = str(value.get("sessionId") or result.get("sessionId") or "")
        if not SESSION.fullmatch(session_id):
            raise HubError("hub_session_id_missing_check_runs")
        caps = value.get("capabilities") or {}
        if not isinstance(caps,dict):
            caps = {}
        # W3C session capabilities are returned by the cloud Android provider.
        # Never infer ARM64 or provider termination from the success of an
        # activation command alone.
        platform_version = str(caps.get("platformVersion") or "")
        device_id = str(caps.get("appium:udid") or "")
        provider_id = str(caps.get("spawndroid:sessionId") or "")
        proof = False
        teardown_ack = False
        webdriver_gone = False
        report = {}
        try:
            pkg = caps.get("spawndroid:appPackage")
            if pkg != KWAIPKG:
                raise HubError("installed_package_mismatch")
            if not device_id or not platform_version:
                raise HubError("android_device_capabilities_unverified")
            activation = self.send("POST", "/session/" + session_id +
                                   "/execute/sync", {
                "script": "mobile: activateApp",
                "args": [{"appId": KWAIPKG}]
            })
            if activation.get("value") is not None:
                raise HubError("activation_response_unexpected")
            foreground = self.send("POST", "/session/" + session_id +
                                   "/execute/sync", {
                "script": "mobile: queryAppState",
                "args": [{"appId": KWAIPKG}]
            })
            if foreground.get("value") != 4:
                raise HubError("kwai_not_in_foreground")
            source = self.send("GET", "/session/" + session_id + "/source")
            xml = source.get("value")
            if not isinstance(xml, str) or "<hierarchy" not in xml:
                raise HubError("kwai_ui_source_unverified")
            proof = True
            report = {
                "session_id": session_id,
                "provider_session_id": provider_id,
                "android_device_id": device_id,
                "android_version": platform_version,
                "android_arm64_verified": False,
                "kwai_package": KWAIPKG,
                "kwai_foreground_verified": True,
                "webdriver_ui_tree_verified": True,
                "account_authenticated": False,
                "publication_attempted": False,
            }
        finally:
            try:
                self.send("DELETE", "/session/" + session_id +
                          "?result=" + ("passed" if proof else "failed"))
                teardown_ack = True
            except HubError:
                pass
            if teardown_ack:
                # DELETE acknowledgement alone does not establish teardown.
                # A second read must observe the W3C invalid-session result.
                try:
                    self.send("GET", "/session/" + session_id)
                except HubError as exc:
                    webdriver_gone = str(exc) == "session_not_found"
            if not webdriver_gone:
                raise HubError("hub_teardown_unverified")
        report["webdriver_session_terminated"] = True
        # The provider's device-minute reservation requires an independent
        # SpawnDroid REST/console readback. Expose this separate gate honestly.
        report["provider_device_termination_verified"] = False
        return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slug",default=os.getenv("SPAWNDROID_KWAI_ARTIFACT_SLUG",""))
    p.add_argument("--execute",action="store_true")
    args=p.parse_args()
    token=os.getenv("SPAWNDROID_CI_TOKEN","")
    if not token:
        print("KWAI_STABLE_HUB=TOKEN_NOT_CONFIGURED")
        return 0 if not args.execute else 20
    if not args.execute:
        print("KWAI_STABLE_HUB=CONFIGURED_NOT_STARTED")
        return 0
    try:
        client=SpawnDroidHub(token)
        proof=client.verify_kwai_once(
            args.slug,
            enable=os.getenv("SPAWNDROID_HUB_CANARY_ENABLED")=="1",
            free_hobby=os.getenv("SPAWNDROID_HOBBY_FREE_CONFIRMED")=="1")
        print("KWAI_STABLE_HUB=APP_VERIFIED_WEBDRIVER_CLOSED_PROVIDER_UNVERIFIED")
        print("KWAI_STABLE_HUB_EVIDENCE="+json.dumps(proof,sort_keys=True))
        print("KWAI_PUBLICATION_ATTEMPTED=0")
        return 22
    except HubError as exc:
        print("KWAI_STABLE_HUB="+str(exc))
        print("KWAI_PUBLICATION_ATTEMPTED=0")
        return 21


if __name__=="__main__":
    sys.exit(main())
