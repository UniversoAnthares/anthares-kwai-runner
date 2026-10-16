#!/usr/bin/env python3
import os
import subprocess
import sys

PROJECT = "UniversoAnthares/anthares-kwai-runner"
ARCHIVE = "archive/gitlab-independent-20261016"

def run(*args, check=True):
    p = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.stdout:
        print(p.stdout, end="")
    if p.returncode and check:
        if p.stderr:
            print(p.stderr, file=sys.stderr, end="")
        raise SystemExit(p.returncode)
    return p

auth = os.environ.get("GL_AUTH", "").strip()
if not auth:
    raise SystemExit("missing GitLab authentication")

url = f"https://oauth2:{auth}@gitlab.com/{PROJECT}.git"
run("git", "config", "user.name", "Anthares GitHub-to-GitLab Sync")
run("git", "config", "user.email", "sync@anthares.invalid")

# Refresh GitLab refs without altering GitHub.
run("git", "fetch", "--no-tags", url,
    "+refs/heads/main:refs/remotes/gitlab/main",
    f"+refs/heads/{ARCHIVE}:refs/remotes/gitlab/archive")

# Keep an exact, disposable tracking branch of GitHub main in GitLab.
run("git", "push", "--force", url, "HEAD:refs/heads/github-main")

# GitLab main is the integration branch. Start from its current tip so all
# GitLab-only history is retained. GitLab wins only when the same lines conflict.
run("git", "switch", "--force-create", "gitlab-sync", "refs/remotes/gitlab/main")
ancestor = run("git", "merge-base", "--is-ancestor", "origin/main", "HEAD", check=False)
if ancestor.returncode != 0:
    merge = run("git", "merge", "--no-edit", "-X", "ours", "origin/main", check=False)
    if merge.returncode != 0:
        run("git", "status", "--short", check=False)
        run("git", "merge", "--abort", check=False)
        raise SystemExit("unresolved merge conflict; GitLab main left unchanged")

# Never force the integration branch. A concurrent GitLab write makes this fail
# safely and the next scheduled run will retry from the new tip.
run("git", "push", url, "HEAD:refs/heads/main")

# Verify both upstream inclusion and preservation of the archived GitLab tip.
run("git", "fetch", "--no-tags", url,
    "+refs/heads/main:refs/remotes/gitlab/main",
    "+refs/heads/github-main:refs/remotes/gitlab/github-main",
    f"+refs/heads/{ARCHIVE}:refs/remotes/gitlab/archive")
run("git", "merge-base", "--is-ancestor", "origin/main", "refs/remotes/gitlab/main")
run("git", "merge-base", "--is-ancestor", "refs/remotes/gitlab/archive", "refs/remotes/gitlab/main")
if run("git", "rev-parse", "refs/remotes/gitlab/github-main").stdout.strip() != run("git", "rev-parse", "origin/main").stdout.strip():
    raise SystemExit("github-main tracking branch mismatch")
print("GITLAB_SYNC=PASS")
