#!/usr/bin/env python3
"""Isolated SpawnDroid Hobby / Kwai cloud Android compatibility adapter.

Only a one-shot Android launch/probe is supported. This deliberately has NO
Kwai publication path, NO login automation, NO Neon lease and NO account
cutover. Free Hobby sessions are ephemeral; a successful boot is not a real
publication or a persistent authenticated Android device.

API contracts: https://docs.spawndroid.io/docs/api/
Pricing: https://docs.spawndroid.io/docs/plans/
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request

API = "https://app.spawndroid.io"
EXPECTED_PACKAGE = "com.kwai.video"  # Kwai official APK, repo's existing Android contract.
EXPECTED_ACCOUNT = "universoanthares"
MAX_CANARY_SECONDS = 180
ARTIFACT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{1,110}$")
SESSION = re.compile(r"^sess_[A-Za-z0-9_-]{3,90}$")


class SpawnError(Exception):
    """Sanitized diagnostic; never store an HTTP body or an API token."""


class SpawnClient:
    def __init__(self, key: str, transport=None):
        if not key:
            raise SpawnError("api_key_missing")
        self.key = key
        self.transport = transport or urllib.request.urlopen

    def api(self, method: str, path: str, payload=None, idem=None):
        if not path.startswith("/api/") or "?" in path or ".." in path:
            raise SpawnError("unsupported_path")
        data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
        headers = {
            "Authorization": "Bearer " + self.key,
            "Accept": "application/json",
        }
        if data is not None:
            headers["Content-Type"] = "application/json"
        if idem:
            headers["Idempotency-Key"] = idem
        request = urllib.request.Request(API + path, method=method,
                                         data=data, headers=headers)
        try:
            with self.transport(request, timeout=20) as response:
                result = json.loads(response.read(65536).decode("utf-8"))
                if not isinstance(result, dict):
                    raise SpawnError("unexpected_response")
                return result
        except urllib.error.HTTPError as exc:
            # Error bodies and the original request can expose account data.
            codes = {401: "unauthorized", 402: "free_quota_exhausted",
                     403: "scope_or_plan_denied", 404: "not_found",
                     409: "idempotency_in_progress", 429: "concurrency_limit",
                     502: "device_host_unavailable", 503: "service_unavailable"}
            raise SpawnError(codes.get(exc.code, "http_" + str(exc.code))) from None
        except urllib.error.URLError:
            raise SpawnError("transport_unavailable") from None
        except (ValueError, UnicodeError):
            raise SpawnError("invalid_json_response") from None

    def inventory(self):
        apps = self.api("GET", "/api/apps").get("apps")
        profiles = self.api("GET", "/api/device-profiles").get("profiles")
        if not isinstance(apps, list) or not isinstance(profiles, list):
            raise SpawnError("inventory_shape_invalid")
        return {"apps": apps, "profiles": profiles}

    @staticmethod
    def _app_package(app):
        if not isinstance(app, dict):
            return ""
        package = app.get("packageName") or app.get("package")
        manifest = app.get("manifest")
        if not package and isinstance(manifest, dict):
            package = manifest.get("packageName") or manifest.get("package")
        if isinstance(package, dict):
            package = package.get("name")
        return str(package or "")

    def find_kwai_artifact(self, artifact_id: str, apps):
        if not ARTIFACT.fullmatch(artifact_id):
            raise SpawnError("artifact_id_invalid")
        candidates = [app for app in apps if isinstance(app, dict) and
                      artifact_id in (str(app.get("id") or ""),
                                      str(app.get("slug") or ""))]
        if len(candidates) != 1:
            raise SpawnError("kwai_artifact_not_registered")
        if self._app_package(candidates[0]) != EXPECTED_PACKAGE:
            raise SpawnError("kwai_package_unverified")
        return candidates[0]

    def canary(self, artifact_id: str, *, run_enabled=False,
               hobby_free_confirmed=False, max_seconds=MAX_CANARY_SECONDS,
               clock=time.monotonic, sleep=time.sleep):
        # Both gates are required even if the provider advertises a Free plan.
        # The adapter has no API for proving the workspace's actual billing tier.
        if not run_enabled or not hobby_free_confirmed:
            raise SpawnError("manual_canary_gate_disabled")
        if not 1 <= max_seconds <= MAX_CANARY_SECONDS:
            raise SpawnError("canary_duration_invalid")
        inventory = self.inventory()
        app = self.find_kwai_artifact(artifact_id, inventory["apps"])
        if not any(isinstance(p,dict) and p.get("id")=="android-14-phone"
                   for p in inventory["profiles"]):
            raise SpawnError("android_14_profile_unavailable")
        session_id = ""
        started = False
        status = "failed"
        deadline = clock() + max_seconds
        try:
            # Idempotency key prevents duplicate sessions if a request is
            # retried externally, but this code never retries an uncertain POST.
            result = self.api("POST", "/api/v1/sessions",
                              {"artifactId":artifact_id,
                               "profileId":"android-14-phone"},
                              idem="kwai-probe-" + uuid.uuid4().hex)
            started = True
            session_id = str(result.get("sessionId") or "")
            if not SESSION.fullmatch(session_id):
                raise SpawnError("created_session_id_invalid")
            while clock() < deadline:
                detail = self.api("GET", "/api/v1/sessions/" + session_id)
                state = str(detail.get("state") or "").lower()
                if state == "ready":
                    package = detail.get("package")
                    if isinstance(package, dict):
                        package = package.get("package")
                    if package != EXPECTED_PACKAGE:
                        raise SpawnError("session_package_mismatch")
                    device = detail.get("device") or {}
                    if not isinstance(device, dict) or not device.get("serial"):
                        raise SpawnError("android_device_unverified")
                    status = "android_boot_verified"
                    return {"status": status, "app_package": EXPECTED_PACKAGE,
                            "account_tested": False, "published": False,
                            "session_closed_on_return": True}
                if state in ("failed", "error", "stopped", "terminated"):
                    raise SpawnError("cloud_android_launch_failed")
                sleep(min(4, max(0, deadline-clock())))
            raise SpawnError("android_boot_deadline")
        finally:
            if started and SESSION.fullmatch(session_id):
                try:
                    self.api("DELETE", "/api/v1/sessions/" + session_id,
                             {"result": "passed" if status=="android_boot_verified"
                              else "failed"})
                except SpawnError:
                    # This cannot be reported as a finished/clean session.
                    # Never attempt another start until the provider is checked.
                    raise SpawnError("session_teardown_unverified") from None


def main():
    parser = argparse.ArgumentParser(description="Read-only SpawnDroid Kwai preflight / gated one-shot Android canary")
    parser.add_argument("--mode",choices=("status","canary"),default="status")
    parser.add_argument("--artifact-id",default=os.getenv("SPAWNDROID_KWAI_ARTIFACT_ID",""))
    parser.add_argument("--max-seconds",type=int,default=150)
    args=parser.parse_args()
    key=os.getenv("SPAWNDROID_API_KEY","").strip()
    if not key:
        print("KWAI_SPAWNDROID=NEEDS_WORKSPACE_API_KEY")
        return 0 if args.mode=="status" else 20
    try:
        api=SpawnClient(key)
        if args.mode=="status":
            data=api.inventory()
            kwai=sum(1 for a in data["apps"]
                     if api._app_package(a)==EXPECTED_PACKAGE)
            print("KWAI_SPAWNDROID=API_READ_OK")
            print("KWAI_KWAI_ARTIFACTS="+str(kwai))
            print("KWAI_ANDROID14_PROFILE="+str(any(
                isinstance(p,dict) and p.get("id")=="android-14-phone"
                for p in data["profiles"])).lower())
            print("KWAI_PUBLICATION_ATTEMPTED=0")
            return 0
        if os.getenv("SPAWNDROID_HOBBY_FREE_CONFIRMED")!="1":
            raise SpawnError("free_plan_confirmation_missing")
        if os.getenv("SPAWNDROID_EXPERIMENTAL_CANARY_ENABLED")!="1":
            raise SpawnError("canary_not_authorized")
        if not args.artifact_id:
            raise SpawnError("kwai_artifact_missing")
        result=api.canary(args.artifact_id,run_enabled=True,
                          hobby_free_confirmed=True,max_seconds=args.max_seconds)
        print("KWAI_SPAWNDROID="+result["status"].upper())
        print("KWAI_PUBLICATION_ATTEMPTED=0")
        return 0
    except SpawnError as exc:
        print("KWAI_SPAWNDROID="+str(exc))
        print("KWAI_PUBLICATION_ATTEMPTED=0")
        return 25


if __name__=="__main__":
    sys.exit(main())
