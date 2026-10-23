#!/usr/bin/env python3
"""Read-only X API OAuth 1.0a probe.

No credential values or Authorization headers are printed. The script exits 0 only
for a 2xx response, so green CI means a genuinely usable authenticated read route.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


def pct(value: str) -> str:
    return urllib.parse.quote(str(value), safe="~-._")


def require(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        print(f"BLOCKED_MISSING_SECRET name={name}")
        raise SystemExit(90)
    return value


def compact_body(raw: bytes) -> str:
    text = raw.decode("utf-8", "replace")[:4000]
    try:
        data = json.loads(text)
    except Exception:
        return " ".join(text.split())[:800]

    safe = {}
    if isinstance(data, dict):
        for key in ("title", "detail", "type", "status"):
            if key in data:
                safe[key] = data[key]
        if "errors" in data:
            errors = []
            src = data["errors"] if isinstance(data["errors"], list) else [data["errors"]]
            for item in src[:5]:
                if isinstance(item, dict):
                    errors.append({k: item.get(k) for k in ("code", "message", "title", "detail") if k in item})
                else:
                    errors.append(str(item)[:200])
            safe["errors"] = errors
        if "data" in data and isinstance(data["data"], dict):
            safe["data_keys"] = sorted(data["data"].keys())
            for key in ("id", "username", "name"):
                if key in data["data"]:
                    safe.setdefault("data_public", {})[key] = data["data"][key]
    return json.dumps(safe, ensure_ascii=False, sort_keys=True)[:1200]


def main() -> int:
    consumer_key = require("X_API_KEY")
    consumer_secret = require("X_API_SECRET")
    access_token = require("X_ACCESS_TOKEN")
    access_secret = require("X_ACCESS_TOKEN_SECRET")

    host = os.environ.get("PROBE_HOST", "api.twitter.com")
    path_query = os.environ.get("PROBE_PATH_QUERY", "/1.1/account/verify_credentials.json?skip_status=true")
    include_version = os.environ.get("PROBE_OAUTH_VERSION", "1") == "1"
    probe_id = os.environ.get("PROBE_ID", "unknown")

    if not path_query.startswith("/"):
        print("INVALID_PROBE_PATH")
        return 91
    if host not in {"api.twitter.com", "api.x.com"}:
        print("INVALID_PROBE_HOST")
        return 92

    url = f"https://{host}{path_query}"
    parsed = urllib.parse.urlsplit(url)
    base_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
    query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)

    oauth = {
        "oauth_consumer_key": consumer_key,
        "oauth_nonce": secrets.token_hex(18),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": access_token,
    }
    if include_version:
        oauth["oauth_version"] = "1.0"

    signature_pairs = query_pairs + list(oauth.items())
    signature_pairs.sort(key=lambda kv: (pct(kv[0]), pct(kv[1])))
    normalized = "&".join(f"{pct(k)}={pct(v)}" for k, v in signature_pairs)
    base_string = "&".join(("GET", pct(base_url), pct(normalized)))
    signing_key = f"{pct(consumer_secret)}&{pct(access_secret)}".encode()
    signature = base64.b64encode(hmac.new(signing_key, base_string.encode(), hashlib.sha1).digest()).decode()
    oauth["oauth_signature"] = signature

    auth = "OAuth " + ", ".join(f'{pct(k)}="{pct(v)}"' for k, v in sorted(oauth.items()))
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Authorization": auth,
            "Accept": "application/json",
            "User-Agent": "Anthares-X-OAuth-Probe/1.0",
        },
    )

    print(f"probe={probe_id} host={host} oauth_version={'on' if include_version else 'off'} path={parsed.path} query_keys={[k for k, _ in query_pairs]}")
    print("secrets_present=X_API_KEY,X_API_SECRET,X_ACCESS_TOKEN,X_ACCESS_TOKEN_SECRET")

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            status = int(resp.status)
            body = resp.read(65536)
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        body = exc.read(65536)
    except Exception as exc:
        print(f"TRANSPORT_ERROR type={type(exc).__name__} detail={str(exc)[:300]}")
        return 93

    print(f"http_status={status}")
    print(f"response={compact_body(body)}")

    if 200 <= status < 300:
        print("VERDICT=AUTH_READ_ROUTE_OK")
        return 0
    if status == 401:
        print("VERDICT=AUTH_REJECTED_401")
        return 41
    if status == 403:
        print("VERDICT=AUTH_OR_ACCESS_BLOCKED_403")
        return 43
    if status == 429:
        print("VERDICT=RATE_LIMITED_429")
        return 49
    if status in (404, 410):
        print("VERDICT=ENDPOINT_UNAVAILABLE")
        return 44
    print(f"VERDICT=HTTP_{status}_UNUSABLE")
    return 40


if __name__ == "__main__":
    sys.exit(main())
