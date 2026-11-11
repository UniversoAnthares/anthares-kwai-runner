# AOI7 Forgejo — public GitHub origin authentication isolation
STATUS: RUNNING
OWNER: chatgpt-20261111-public-kwai-source
UTC: 2026-11-11T14:21Z
BRANCH: fix/hostinger-public-kwai-github-origin-20261111
BASE_SHA: 0b8ab8ca1037c8aa7de4d007636863853930f9fc
SOURCE_FILE: tools/hostinger/git-mirror-hostinger.py
CURRENT_BLOB: c90bfecccb99fe1c86c40a372c85ef36c60b3539
EVIDENCE: Hostinger hPanel authenticated, git mirror receipt 2026-11-11T14:00:14Z has 15 entries with single BLOCKED_GITHUB_SOURCE_NOT_AUTHORIZED_OR_UNAVAILABLE for public repo UniversoAnthares/anthares-kwai-runner. GitHub connector confirms repo id 1406232047, visibility public and pull rights. Other 13 remote sources verified at 14:00. Existing Python run() sets GIT_ASKPASS to GitHub token helper for all GitHub sources, including this public clone. No independent raw stderr in receipt; cause remains unknown.
SCOPE: Safely force anonymous (GIT_ASKPASS=/bin/false) only for public HTTPS source of anthares-kwai-runner; preserve existing private credentials, deploy keys, 15 repositories and mirror refs. Add allowlisted failure classification for no-auth GitHub public source without logging URL/token/stderr; do not expose sensitive data.
SUCCESS: isolate public repo from potentially invalid credential helper; script tests in isolation; deploy exact file by authenticated hPanel in minimized independent Chrome session; verify sha and next scheduled full source ref parity.
FAILURE: source still inaccessible; leave a precise opaque diagnostic with no secrets and preserve all other services.
RESTRICTIONS: no Hostinger shell/SSH bypass of previous denial; no Github actions runner; no process kill, no forced git push/prune, no fee, no browser mouse/keyboard user interference. 
