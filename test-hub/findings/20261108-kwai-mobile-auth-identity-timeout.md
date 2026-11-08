# Kwai hosted mobile authentication reached owner handoff
STATUS: PARTIAL
AREA: kwai-login
SUPERSEDES: 20261108-lease-kwai-login-adb-path.md
LEASE_CLOSED: 20261108-lease-kwai-login-adb-path.md
GOVERNANCE_MANIFEST: 84905aefc5589d17
RUN: 42519025289
BOOTSTRAP_JOB: 128848226014
HEAD: 2995bf621391b56ddfdf3956fd2eb60ce87bf705
PROVEN: Hosted Android boot, official APK install, mapped scrcpy window, protected noVNC handoff while the job was active, and tunnel cleanup. The unauthenticated closed endpoint returned HTTP 530.
OBSERVED: The owner reported completing login. The job emitted KWAI_MOBILE_AUTH_TIMEOUT=1, exit 72. The wait step retained no privacy-safe reason code from the probe, so the cause of the missing identity proof is undetermined.
VAULT: Initial read was absent. The seal step was skipped. No session was written by this run.
RESTORES: Both independent jobs were skipped, so persistence was not tested.
SCOPE: Publish was skipped. No queue access or Windows executor. Agent-owned browser tabs were closed after the browser rejected the Basic authentication challenge. No access details are included in this record.
