#!/usr/bin/env bash
set -euo pipefail
provider="${1:?provider required}"
case "$provider" in
  gitlab) target="${ANTHARES_GITLAB_PUSH_URL:-}" ;;
  codeberg) target="${ANTHARES_CODEBERG_PUSH_URL:-}" ;;
  *) echo "unsupported provider" >&2; exit 64 ;;
esac
[ -n "$target" ] || { echo "TARGET_NOT_CONFIGURED provider=$provider"; exit 78; }
src="${ANTHARES_GITHUB_SOURCE_URL:-https://github.com/UniversoAnthares/anthares-kwai-runner.git}"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
git clone --mirror "$src" "$tmp/repo.git"
cd "$tmp/repo.git"
before="$(git show-ref | sha256sum | awk '{print $1}')"
git remote add target "$target"
git push --prune target 'refs/heads/*:refs/heads/*'
git push target 'refs/tags/*:refs/tags/*'
after="$(git show-ref | sha256sum | awk '{print $1}')"
[ "$before" = "$after" ] || { echo "LOCAL_REFSET_CHANGED"; exit 70; }
echo "SYNC_PROVEN provider=$provider head=$(git rev-parse refs/heads/main)"
