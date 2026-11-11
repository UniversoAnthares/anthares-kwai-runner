# AOI7 Hostinger Forgejo keepalive — inherited FD9 lock
STATUS: RUNNING
AREA: architecture/forgejo-daemon-hostinger-keepalive-lock
OWNER: chatgpt-20261111-inherited-lock
DATE_UTC: 2026-11-11T13:29Z
BRANCH: fix/forgejo-keepalive-inherited-lock-20261111
BASE_SHA: 7ab9f961b68f02f1819b52fcc8edaff4cdfc20e4
GOVERNANCE_SHA: 821bdcb8d8479b0c28371a6f058b4b32d86a3fa1
SCRIPT_CURRENT_BLOB: 966e539447a814da72f8db0c8a682cef1603fe0b
TEST_CURRENT_BLOB: 0d4ee77296b91a0c4e4c5317e5d18feb3989c717
PREVIOUS_LEASES: closed (20261111-hostinger-drive-backup-cron-dedup-proven.md; 20261111-forgejo-hpanel-daemon-recovery-proven.md)
EVIDENCE: Authenticated Hostinger hPanel File Browser, private ~/.anthares-forgejo/forgejo.log 2.76MiB, latest lines through 2026-11-11T13:17:06Z, shows Forgejo started 12:25:05Z on Unix socket pid 538092, GET /api/v1/version 200; Git transport HTTP 200 at 13:17. Mirror status at 12:30:20Z recorded 15 repos, zero failures and 13 nonempty+2 empty; Gitlab extra mirror 12:30:23Z 5 sources zero failures though refs divergence in tiktok-forgejo must not be hidden. Since the 12:25:05 start, log shows no subsequent /api/v1/version health probes despite */5 cron installed and no fresh reliable output in hPanel.
FAULT_CANDIDATE: keepalive script opens fd9 and obtains exclusive flock, then starts Forgejo via nohup without closing descriptor 9. The daemon inherits the lock and blocks subsequent invocations from reaching healthy(). Safe fix: check API health before acquiring lock; still recheck once lock acquired; use 9>&- for child to prevent inherited lock. Preserve process, socket, Git refs, all crons.
SCOPE: only tools/forgejo_keepalive.sh, tests/test_forgejo_keepalive_safety.py and this Test Hub lease/receipt; no Hostinger SSH/controller evasion, public HTTP origin probing, daemon kill/restart or cross-repo source reset.
ACCEPTANCE: mock isolation reproduces inherited lock issue, new tests prove subsequent healthy invocation succeeds and child has no inherited FD9, existing 7 tests pass, deploy exact corrected content via authorized owner hPanel existing script ONLY, demonstrate a new valid API /api/v1/version entry after deployment with cron cadence.
RISK: running old daemon may hold lock FD9 until natural restart; early healthy check must work through that and safely avoid competition.
NO_NEW_COST: true
NO_PUBLICATIONS: true
