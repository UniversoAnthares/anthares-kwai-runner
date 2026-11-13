#!/usr/bin/env python3
"""Two-account Neon queue transport for a FUTURE persistent Android host.

Credentials are exclusively on the approved cloud host; this program cannot
run with GitHub OIDC or physical-phone secrets. Never retries uncertain writes.
The Neon server must separately enable and authorize this actor before use.
No APK install, login, publishing or service activation is performed here.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ENDPOINT = "https://br-crimson-unit-b89nau08-cortesqueue.compute.c-14.us-east-1.aws.neon.tech/"
ACCOUNTS = {"lucasrosalem": "kwai:lucasrosalem",
            "universoanthares": "kwai:universoanthares"}
ACTIONS = {"lease": "kwai-lease", "renew": "kwai-renew",
           "start": "kwai-start", "confirm": "kwai-confirm",
           "fail": "kwai-fail"}
JOB_ID = re.compile(r"^kwai-cortes-[A-Za-z0-9._:-]{3,145}$")


class CloudQueueError(Exception):
    pass


def credential(environ=None):
    env = os.environ if environ is None else environ
    value = env.get("KWAI_PERSISTENT_CLOUD_TOKEN", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}", value):
        raise CloudQueueError("KWAI_PERSISTENT_CLOUD_TOKEN_UNCONFIGURED")
    return value


def envelope(account, action, body):
    if account not in ACCOUNTS or action not in ACTIONS or not isinstance(body, dict):
        raise CloudQueueError("KWAI_CLOUD_INPUT_INVALID")
    data = dict(body)
    if data.get("target_key", ACCOUNTS[account]) != ACCOUNTS[account]:
        raise CloudQueueError("KWAI_CLOUD_TARGET_MISMATCH")
    if data.get("expected_account", account) != account:
        raise CloudQueueError("KWAI_CLOUD_ACCOUNT_MISMATCH")
    data.update(target_key=ACCOUNTS[account], expected_account=account)
    if action == "lease":
        ttl = data.get("lease_seconds", 180)
        if type(ttl) is not int or not 60 <= ttl <= 600:
            raise CloudQueueError("KWAI_CLOUD_LEASE_TTL_INVALID")
        data["lease_seconds"] = ttl
    else:
        job = data.get("id")
        generation = data.get("lease_generation")
        if not isinstance(job, str) or not JOB_ID.fullmatch(job) or (
                type(generation) is not int or generation < 1):
            raise CloudQueueError("KWAI_CLOUD_FENCE_INVALID")
        if action == "renew":
            ttl = data.get("lease_seconds", 180)
            if type(ttl) is not int or not 60 <= ttl <= 600:
                raise CloudQueueError("KWAI_CLOUD_RENEW_TTL_INVALID")
            data["lease_seconds"] = ttl
        elif action == "confirm":
            proof = data.get("confirmation_evidence")
            if (not isinstance(proof, dict) or
                    proof.get("account") != account or
                    not re.fullmatch(r"[a-f0-9]{64}",
                                     str(proof.get("attestation_hmac", ""))) or
                    not isinstance(data.get("remote_id"), str) or
                    not data["remote_id"]):
                raise CloudQueueError("KWAI_CLOUD_INDEPENDENT_CONFIRMATION_REQUIRED")
        elif action == "fail":
            # Unless absence of a commit is independently proven, the
            # operation may have published; quarantine it, never retry.
            if data.get("published_possible") is not True:
                raise CloudQueueError("KWAI_CLOUD_FAIL_MUST_QUARANTINE")
    return data


def request_once(account, action, body, *, token=None):
    payload = envelope(account, action, body)
    secret = credential() if token is None else token
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}", secret):
        raise CloudQueueError("KWAI_CLOUD_TOKEN_INVALID")
    url = ENDPOINT + "?" + urlencode({"action": ACTIONS[action]})
    req = Request(url,
                  data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
                  headers={"Authorization": "Bearer " + secret,
                           "Content-Type": "application/json",
                           "Accept": "application/json"},
                  method="POST")
    try:
        with urlopen(req, timeout=30) as response:
            result = json.load(response)
    except HTTPError as exc:
        raise CloudQueueError("KWAI_CLOUD_HTTP_" + str(exc.code)) from None
    except (URLError, TimeoutError, OSError, ValueError, UnicodeError):
        raise CloudQueueError("KWAI_CLOUD_OUTCOME_UNKNOWN_STOP") from None
    if not isinstance(result, dict) or result.get("ok") is not True:
        raise CloudQueueError("KWAI_CLOUD_BACKEND_REJECTED")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=tuple(ACTIONS))
    parser.add_argument("--account", required=True, choices=tuple(ACCOUNTS))
    parser.add_argument("--json", default="{}")
    parser.add_argument("--lease-file", default="kwai-cloud-lease.json")
    args = parser.parse_args()
    body = json.loads(Path(args.json[1:]).read_text(encoding="utf-8")
                      if args.json.startswith("@") else args.json)
    reply = request_once(args.account, args.action, body)
    if args.action == "lease":
        job = reply.get("job")
        if job is None:
            print("KWAI_CLOUD_LEASE=NONE")
            return 0
        if not isinstance(job, dict):
            raise CloudQueueError("KWAI_CLOUD_LEASE_JOB_INVALID")
        payload = job.get("payload")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (ValueError, TypeError):
                raise CloudQueueError("KWAI_CLOUD_LEASE_PAYLOAD_INVALID") from None
        if not isinstance(payload, dict):
            raise CloudQueueError("KWAI_CLOUD_LEASE_PAYLOAD_INVALID")
        account = args.account
        gen = job.get("lease_generation")
        if (type(gen) is int and gen >= 1):
            pass
        elif isinstance(gen, str) and re.fullmatch(r"[1-9][0-9]{0,17}", gen):
            gen = int(gen)
        else:
            raise CloudQueueError("KWAI_CLOUD_LEASE_GENERATION_INVALID")
        if (job.get("target_key") != ACCOUNTS[account] or
                payload.get("expected_account") != account or
                not JOB_ID.fullmatch(str(job.get("id", "")))):
            raise CloudQueueError("KWAI_CLOUD_LEASE_IDENTITY_MISMATCH")
        job["lease_generation"] = gen
        job["payload"] = payload
        dest = Path(args.lease_file)
        # O_EXCL + 0600 before any bytes are written; preserve unknown
        # outcomes rather than overwriting the previous lease receipt.
        fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(job, f, separators=(",", ":"))
        print("KWAI_CLOUD_LEASE=ACQUIRED")
    else:
        print("KWAI_CLOUD_" + args.action.upper() + "=ACK")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (CloudQueueError, ValueError, KeyError, OSError) as exc:
        print(str(exc).splitlines()[0][:160], file=sys.stderr)
        sys.exit(89)
