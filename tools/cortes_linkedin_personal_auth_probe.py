#!/usr/bin/env python3
"""LinkedIn personal token read-only verification. Never emit token or member PII.

A valid response confirms the token can identify the consenting member. This
probe deliberately makes no publication or queue requests.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request

_USERINFO = "https://api.linkedin.com/v2/userinfo"
_MEMBER_ID = re.compile(r"[A-Za-z0-9_-]{2,200}\Z")


class OAuthProbeFailed(RuntimeError):
    pass


def verify(token: str, *, opener=urllib.request.urlopen) -> bool:
    if not token or any(ch in token for ch in "\r\n\x00") or len(token) < 20:
        raise OAuthProbeFailed("TOKEN_MISSING_OR_MALFORMED")
    request = urllib.request.Request(
        _USERINFO,
        headers={"Authorization": "Bearer " + token, "Accept": "application/json",
                 "User-Agent": "anthares-linkedin-personal-auth-probe/1"},
        method="GET",
    )
    try:
        with opener(request, timeout=20) as response:
            body = response.read(8192)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise OAuthProbeFailed("TOKEN_NOT_AUTHORIZED") from None
        raise OAuthProbeFailed("LINKEDIN_HTTP_ERROR") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise OAuthProbeFailed("LINKEDIN_UNREACHABLE") from None
    try:
        data = json.loads(body)
        sub = data.get("sub")
    except (ValueError, TypeError, AttributeError):
        raise OAuthProbeFailed("INVALID_USERINFO_RESPONSE") from None
    if not isinstance(sub, str) or not _MEMBER_ID.fullmatch(sub):
        raise OAuthProbeFailed("PERSON_ID_NOT_VERIFIED")
    # Never return member ID, name, email, or a generated URN to stdout.
    return True


def main() -> int:
    try:
        if not verify(os.getenv("LINKEDIN_PERSONAL_ACCESS_TOKEN", "")):
            raise OAuthProbeFailed("AUTH_UNVERIFIED")
        print("LINKEDIN_PERSONAL_OAUTH_READ_ONLY=PASS")
        return 0
    except OAuthProbeFailed as exc:
        print("LINKEDIN_PERSONAL_OAUTH_READ_ONLY=BLOCKED:" + str(exc))
        return 2
    except Exception:
        print("LINKEDIN_PERSONAL_OAUTH_READ_ONLY=BLOCKED:UNEXPECTED_ERROR")
        return 2


if __name__ == "__main__":
    sys.exit(main())
