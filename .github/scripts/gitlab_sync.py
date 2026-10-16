#!/usr/bin/env python3
import os
import subprocess
import sys

PROJECT = "UniversoAnthares/anthares-kwai-runner"
PRESERVED_BRANCH = "archive/gitlab-main-pre-sync-20261016"


def run(*args, check=True):
    p = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.stdout:
        print(p.stdout, end="")
    if p.returncode and check:
        if p.stderr:
            print(p.stderr, file=sys.stderr, end="")
        raise SystemExit(p.returncode)
    return p


def sha(ref):
    return run("git", "rev-parse", ref).stdout.strip()


auth = os.environ.get("GL_AUTH", "").strip()
if not auth:
    raise SystemExit("missing GitLab authentication")

url = f"https://oauth2:{auth}@gitlab.com/{PROJECT}.git"
source_sha = sha("HEAD")
run("git", "config", "user.name", "Anthares GitHub-to-GitLab Sync")
run("git", "config", "user.email", "sync@anthares.invalid")

# Refresh GitLab refs without altering GitHub.
run("git", "fetch", "--no-tags", url,
    "+refs/heads/main:refs/remotes/gitlab/main",
    f"+refs/heads/{PRESERVED_BRANCH}:refs/remotes/gitlab/preserved")

# Exact disposable tracking branch. Force is safe here because this branch exists
# only to represent the GitHub source SHA for each synchronization round.
run("git", "push", "--force", url, f"{source_sha}:refs/heads/github-main")

# GitLab main remains the integration branch and is never force-pushed. Start
# from its current tip so GitLab-only history is retained. On textual conflicts,
# retain the GitLab side; all non-conflicting GitHub changes are still imported.
run("git", "switch", "--force-create", "gitlab-sync", "refs/remotes/gitlab/main")
if run("git", "merge-base", "--is-ancestor", source_sha, "HEAD", check=False).returncode != 0:
    merge = run("git", "merge", "--no-edit", "-X", "ours", source_sha, check=False)
    if merge.returncode != 0:
        run("git", "status", "--short", check=False)
        run("git", "merge", "--abort", check=False)
        raise SystemExit("unresolved merge conflict; GitLab main left unchanged")

# A concurrent GitLab write causes a normal non-fast-forward failure and leaves
# GitLab untouched; the next push/scheduled run retries from the new GitLab tip.
run("git", "push", url, "HEAD:refs/heads/main")

# Verify the exact source handled by this run, not a moving origin/main ref.
run("git", "fetch", "--no-tags", url,
    "+refs/heads/main:refs/remotes/gitlab/main",
    "+refs/heads/github-main:refs/remotes/gitlab/github-main",
    f"+refs/heads/{PRESERVED_BRANCH}:refs/remotes/gitlab/preserved")
run("git", "merge-base", "--is-ancestor", source_sha, "refs/remotes/gitlab/main")
run("git", "merge-base", "--is-ancestor", "refs/remotes/gitlab/preserved", "refs/remotes/gitlab/main")
if sha("refs/remotes/gitlab/github-main") != source_sha:
    raise SystemExit("github-main tracking branch mismatch")
print(f"SOURCE_SHA={source_sha}")
print(f"GITLAB_MAIN_SHA={sha('refs/remotes/gitlab/main')}")
print("PRESERVED_GITLAB_HISTORY=PASS")
print("GITLAB_SYNC=PASS")
