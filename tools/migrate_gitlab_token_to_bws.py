#!/usr/bin/env python3
"""One-time, fail-closed copy of an existing GitHub GitLab token to Anthares Secrets.

Requires a *separate, temporary* write-enabled Bitwarden machine token.
Never prints either credential, the created secret ID, or Bitwarden API replies.
"""
import hmac
import json
import os
import pathlib
import subprocess
import sys

PROJECT_ID = "a2e8f606-69c5-4d44-80d8-b4e800e279c6"
KEY = "ANTHARES_GITLAB_TOKEN"
BIN = os.environ.get("BWS_BIN", "/tmp/anthares-bws/bws")
stage = "PRECHECK"


def bws(*args):
    env = os.environ.copy()
    env["BWS_ACCESS_TOKEN"] = os.environ["BWS_MIGRATION_WRITE_TOKEN"].strip()
    command = [BIN, "--output", "json", "secret", *args]
    completed = subprocess.run(command, env=env, capture_output=True, text=True, timeout=45, check=False)
    if completed.returncode:
        raise RuntimeError("BWS_COMMAND_FAILED")
    return json.loads(completed.stdout)


def main():
    global stage
    source = os.environ.get("GITLAB_TOKEN", "").strip()
    writer = os.environ.get("BWS_MIGRATION_WRITE_TOKEN", "").strip()
    env_file = os.environ.get("GITHUB_ENV", "")
    if not source or not writer or not env_file:
        print("BWS_MIGRATION_REQUIRED_CREDENTIAL_UNAVAILABLE")
        return 2
    stage = "LIST"
    secrets = bws("list", PROJECT_ID)
    if not isinstance(secrets, list):
        raise RuntimeError("UNEXPECTED_SECRET_LIST_SHAPE")
    existing = [x for x in secrets if isinstance(x, dict) and x.get("key") == KEY]
    if len(existing) > 1:
        raise RuntimeError("DUPLICATE_KEY")
    if existing:
        secret_id = existing[0].get("id")
        action = "ALREADY_EXISTS"
    else:
        stage = "CREATE"
        response = bws("create", KEY, source, PROJECT_ID,
                       "--note", "Anthares GitLab CI control-plane token; GitHub Actions migration")
        if not isinstance(response, dict):
            raise RuntimeError("UNEXPECTED_CREATE_RESULT")
        secret_id = response.get("id")
        action = "CREATED"
    if not isinstance(secret_id, str) or len(secret_id) != 36:
        raise RuntimeError("INVALID_RESULT_ID")
    stage = "VERIFY"
    verified = bws("get", secret_id)
    if not isinstance(verified, dict) or verified.get("projectId") != PROJECT_ID:
        raise RuntimeError("PROJECT_SCOPE_MISMATCH")
    if not hmac.compare_digest(verified.get("value", ""), source):
        raise RuntimeError("TOKEN_VALUE_MISMATCH")
    with open(pathlib.Path(env_file), "a", encoding="utf-8") as out:
        out.write("ANTHARES_MIGRATED_SECRET_ID=" + secret_id + "\n")
    print("BWS_GITLAB_MIGRATION_ACTION=" + action)
    print("BWS_WRITER_SCOPE_VERIFIED=PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("BWS_MIGRATION_FAILURE_STAGE=" + stage)
        print("BWS_MIGRATION_FAILURE_KIND=" + type(exc).__name__)
        sys.exit(1)
