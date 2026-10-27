"""Read-only WordPress CORTES QA authenticated smoke (never prints credentials or payload)."""
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from urllib.parse import urlparse

MAX_BYTES = 2_000_000


def probe(env=None, open_url=None):
    env = os.environ if env is None else env
    site = str(env.get("WP_SITE_URL") or "").strip().rstrip("/")
    user = str(env.get("WP_USERNAME") or "").strip()
    password = "".join(str(env.get("WP_APP_PASSWORD") or "").split())
    if not site or not user or not password:
        return "AUTH_MISSING", 2
    parsed = urlparse(site)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        return "SITE_URL_INVALID", 2
    credentials = base64.b64encode((user + ":" + password).encode("utf-8")).decode("ascii")
    req = urllib.request.Request(
        site + "/wp-json/anthares/v1/cortes/state",
        headers={"Authorization": "Basic " + credentials,
                 "Accept": "application/json",
                 "User-Agent": "AntharesCortesWPQAReadOnly/1"},
        method="GET",
    )
    execute = urllib.request.urlopen if open_url is None else open_url
    try:
        with execute(req, timeout=15) as response:
            if response.status != 200:
                return "HTTP_OTHER", 2
            data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            return "PAYLOAD_TOO_LARGE", 2
        payload = json.loads(data)
        if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
            return "INVALID_SCHEMA", 2
        return "AUTHENTICATED_JSON_ITEMS_" + str(len(payload["items"])), 0
    except urllib.error.HTTPError as exc:
        return ("HTTP_" + str(exc.code) if exc.code in (401, 403, 404, 429) else "HTTP_OTHER"), 2
    except (urllib.error.URLError, OSError, TimeoutError):
        return "NETWORK_ERROR", 2
    except (json.JSONDecodeError, UnicodeDecodeError):
        return "INVALID_JSON", 2


def main():
    code, status = probe()
    print("CORTES_WP_AUTH_SMOKE=" + code)
    return status


if __name__ == "__main__":
    sys.exit(main())
