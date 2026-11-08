# Kwai mobile auth with non-interfering live verification
STATUS: RUNNING
AREA: kwai-login
OWNER: codex-kwai-mobile-auth-passive
LEASE_UNTIL: 2026-11-08T21:22:37Z
HEAD_BASELINE: b099fa9fee9cc4705b3ed825f92c19d51e4343a4
WORKFLOW_BLOB: 6628f060a7e239322d355741484eab78d4401319
PROBE_BLOB: c8b0f9d0addadab4d06c344a77cedff39e265724
GOVERNANCE_MANIFEST: 84905aefc5589d17
SUPERSEDES: 20261108-kwai-mobile-auth-identity-timeout.md
BASELINE_PROVEN: Run 42519025289 reached password-protected noVNC and waited for the identity. The owner reported login but did not confirm that the expected handle was visible. The session was not saved.
FAILED_AVOIDED: Live verification no longer sends taps or gestures while the owner uses Android. It reads a fresh snapshot and logs only fixed reason codes. Never relax exact identity or touch the queue.
SUCCESS_SIGNAL: Expected handle on own Kwai profile, encrypted vault acknowledgement and two separate fresh restores with matching identity.
FAILURE_SIGNAL: Safe observation code and failure to seal or verify both restores.
TEST_VALIDITY: Main, mobile_auth, hosted Android, exact identity check, both restore jobs independent. No active same-chain GitHub or GitLab pipeline observed. Peer files checked, no mirroring.
