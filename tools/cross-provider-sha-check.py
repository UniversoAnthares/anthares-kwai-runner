#!/usr/bin/env python3
"""Read-only GitHub -> GitLab main recovery proof; no Codeberg or ref mutation."""
import json
import os
import re
import subprocess
import sys
import tempfile

BRANCH = os.getenv("ANTHARES_COMPARE_BRANCH", "main")
URLS = {
    "github": os.getenv("ANTHARES_GITHUB_READ_URL") or "https://github.com/UniversoAnthares/anthares-kwai-runner.git",
    "gitlab": os.getenv("ANTHARES_GITLAB_READ_URL") or "https://gitlab.com/UniversoAnthares/anthares-kwai-runner.git",
}
if BRANCH != "main":
    print(json.dumps({"status": "BLOCKED_UNAPPROVED_REF", "branch": BRANCH}))
    sys.exit(2)


def git(*args, timeout=60):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    return subprocess.run(["git", *args], text=True, capture_output=True,
                          timeout=timeout, env=env)


out = {}
for provider, url in URLS.items():
    try:
        result = git("ls-remote", url, "refs/heads/main", timeout=30)
        sha = result.stdout.split()[0].lower() if result.returncode == 0 and result.stdout.strip() else None
        if not sha or not re.fullmatch(r"[0-9a-f]{40}", sha):
            sha = None
        out[provider] = {"state": "UP" if sha else "DOWN", "sha": sha}
    except (OSError, subprocess.TimeoutExpired):
        out[provider] = {"state": "DOWN", "sha": None}

same = all(item["state"] == "UP" for item in out.values()) and out["github"]["sha"] == out["gitlab"]["sha"]
superset = False
if not same and all(item["state"] == "UP" for item in out.values()):
    try:
        with tempfile.TemporaryDirectory(prefix="anthares-gitlab-proof-") as temp:
            if git("init", "-q", temp).returncode == 0:
                fetched = {}
                for provider, url in URLS.items():
                    result = git("-C", temp, "fetch", "--quiet", "--no-tags",
                                 "--filter=blob:none", url, "refs/heads/main", timeout=90)
                    if result.returncode != 0:
                        break
                    fetched[provider] = git("-C", temp, "rev-parse", "FETCH_HEAD").stdout.strip().lower()
                if (fetched.get("github") == out["github"]["sha"]
                        and fetched.get("gitlab") == out["gitlab"]["sha"]):
                    check = git("-C", temp, "merge-base", "--is-ancestor",
                                fetched["github"], fetched["gitlab"])
                    superset = check.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        superset = False

success = same or superset
print(json.dumps({
    "branch": BRANCH,
    "providers": out,
    "all_equal": same,
    "github_main_is_ancestor_of_gitlab": success,
    "gitlab_recovery": "PROVEN_EXACT" if same else "PROVEN_SUPERSET" if superset else "UNVERIFIED",
    "note": "GitLab head is not automatically authorized for publisher execution.",
}, sort_keys=True))
sys.exit(0 if success else 2)
