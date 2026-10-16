# Lease — method 1+2 + method 3 real Kwai canaries, experimental remote path
STATUS: RUNNING
AREA: kwai-publish
DATE: 2026-10-16
RUN: none
JOB: GitHub Actions public Android explicit experiment
COMMIT: pending
SUPERSEDES: 20261016-1351-lease-method12-method3-real-kwai-extend2.md
LEASE_OWNER: chatgpt-method12-method3-experimental-1417Z
LEASE_EXPIRES_UTC: 2026-10-16T14:47:00Z

BASELINE_PROVEN: method 1+2 final master is proven and staged with SHA-256 cd3d23c0fe083575c620a276500335de0fec1d9a615a164a7b0b8c931b18ec28; method 3 fallback is proven end-to-end through full temporary acquisition, final-master proof and full-source deletion with final SHA-256 4ce5276f27484e0e50bebcf06653b9bf021ea655c0888f29fc9f050c3ea8b1d3. Canonical physical -> MEmu publication routing remains unchanged. A separate active kwai-login lease is repairing MEmu storage/ADB and must not be disturbed.

CHANGE: because the user explicitly authorized real publication tests and the canonical Android executors are temporarily unavailable, use the preserved GitHub Android path only as an explicit experiment, never as automatic failover. Restore the protected Kwai session, prove exact account lucasrosalem immediately before publication, publish each canary once, and independently recover its public post URL.

FAILED_AVOIDED: never retry the historical uncertain e2e-20261013-9CIk-I_3VhM-8-98 publication; never re-click after PUBLISH_REQUESTED; never claim success from UI return alone; do not mutate MEmu or kwai-login state; stop the second canary if the first becomes UNCERTAIN.

SUCCESS_SIGNAL: two distinct real public Kwai post URLs on @lucasrosalem, first from method 1+2 master and second from method 3 master, with exact identity proof and one irreversible commit each.

FAILURE_SIGNAL: session restoration/identity proof fails, publication becomes UNCERTAIN, public URL cannot be independently recovered, or any safety gate rejects the operation.

TEST_VALIDITY: GitHub Android is used only under this explicit experimental lease. No automatic routing policy is changed. The two prebuilt masters must match the recorded SHA-256 values before they enter Android.
