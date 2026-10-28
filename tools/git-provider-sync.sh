#!/usr/bin/env bash
# Recover Git from canonical GitHub to GitLab main only.
# No Codeberg, no force push, no deletion of provider branches/tags.
set -euo pipefail
provider="${1:?provider required}"
[ "$provider" = "gitlab" ] || { echo 'CODEBERG_DISABLED_UNSUPPORTED_PROVIDER' >&2; exit 64; }
target="${ANTHARES_GITLAB_PUSH_URL:-}"
[ -n "$target" ] || { echo 'GITLAB_PUSH_URL_NOT_CONFIGURED'; exit 78; }
src="${ANTHARES_GITHUB_SOURCE_URL:-https://github.com/UniversoAnthares/anthares-kwai-runner.git}"
export GIT_TERMINAL_PROMPT=0
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
git clone --quiet --filter=blob:none --no-checkout --single-branch --branch main "$src" "$tmp/repo"
cd "$tmp/repo"
git remote add gitlab "$target"
git -c credential.interactive=never fetch --quiet --filter=blob:none --no-tags gitlab refs/heads/main
source_sha="$(git rev-parse refs/remotes/origin/main)"
target_sha="$(git rev-parse FETCH_HEAD)"
if [ "$source_sha" = "$target_sha" ]; then
  echo "GITLAB_MAIN_EXACT_PARITY_PROVEN=$source_sha"
  exit 0
fi
if git merge-base --is-ancestor "$source_sha" "$target_sha"; then
  # GitLab's safe reconciliation merge is ahead; the exact canonical commit is preserved.
  echo "GITLAB_MAIN_PROVEN_SUPERSET source=$source_sha target=$target_sha"
  exit 0
fi
if ! git merge-base --is-ancestor "$target_sha" "$source_sha"; then
  echo 'GITLAB_DIVERGED_STOP_NO_FORCE_NO_PRUNE' >&2
  exit 2
fi
# Fast-forward-only for a trailing GitLab main. Git itself rejects races/non-FF.
git -c credential.interactive=never push --quiet gitlab "$source_sha:refs/heads/main"
remote="$(git -c credential.interactive=never ls-remote gitlab refs/heads/main)"
actual="$(printf '%s\n' "$remote" | awk '{print $1}')"
[ "$actual" = "$source_sha" ] || { echo 'GITLAB_READBACK_MISMATCH' >&2; exit 2; }
echo "GITLAB_MAIN_FAST_FORWARD_PROVEN=$source_sha"
