# AOI7 Hostinger mirror NPROC transient recovery
STATUS: RUNNING
AREA: architecture/hostinger-forgejo-mirror-python
OWNER: chatgpt-20261111-nproc-mirror
DATE_UTC: 2026-11-11T13:48Z
BASE_SHA: 540bbd18272a1fc45621ac1819098b11baaac5e5
GOVERNANCE_SHA: 821bdcb8d8479b0c28371a6f058b4b32d86a3fa1
PREVIOUS_LEASE: 20261111-aoi7-forgejo-fd9-lock-lease.md (PR #2353 merged; production script SHA 27b95a09e3431a42c51221cc9c7c8b7b73120ff4 verified after reload)
EVIDENCE: Hostinger ~/.anthares-forgejo/git-mirror-hostinger-status.json at 2026-11-11T13:30:27Z: 15 repos, one failure in anthares-kwai-runner state BLOCKED_HOSTING_PROCESS_LIMIT; prior 12:30:20Z: 15 repos and no failures. Hostinger script ~/.anthares-forgejo/git-mirror-hostinger.py Python 7569 chars, serial verify_repo(n), subprocess.run, recognizes stderr "Resource temporarily unavailable" as HOSTING_PROCESS_LIMIT and records BLOCKED_ without any bounded retry. hPanel NPROC was below old cap 80 08:57-09:06 but has transient spikes to cap at half-hour, free boost 80->120 active for 24h.
SCOPE: only source-controlled copy of existing Hostinger mirror script plus one narrow bounded retry for transient HOSTING_PROCESS_LIMIT in the single failing repo anthares-kwai-runner; never force, prune, kill, rewrite refs, change current cron schedule or credentials.
PRECONDITION: in-page source scan for hardcoded secrets before mirroring to private GitHub, sha/content equality to live on read, tests with subprocess mocked or syntactic inspection, exact expected blob verified after production write.
SAFETY: preserve 15 repositories and all refs, existing git concurrency lock, original source GitHub and GitLab histories. Owner-authorized hPanel only, isolated minimized muted profile with CDP navigation; no alternate Hostinger SSH or public HTTPS origin probe after security refusal.
ACCEPTANCE: source versioned, bounded non-duplicating retry on quota only, Python syntax tests, same content verified in Hostinger, zero concurrent cron jobs; next scheduled full mirror must report zero failures to declare synchronization recovered.
NO_NEW_COST: true
NO_PUBLICATIONS: true
