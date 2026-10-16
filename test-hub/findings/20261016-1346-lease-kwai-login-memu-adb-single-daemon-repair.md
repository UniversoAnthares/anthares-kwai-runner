# Lease — Kwai login / MEmu ADB single-daemon repair
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-16
RUN: none
JOB: Anthares Remote
COMMIT: pending
SUPERSEDES: none
LEASE_OWNER: chatgpt-anthares-remote-20261016-1346Z
LEASE_EXPIRES_UTC: 2026-10-16T14:16:00Z

BASELINE_PROVEN: Anthares Remote roundtrip succeeded at 2026-10-16T13:45:51Z. MEmu_4 backend remains running headless, port 127.0.0.1:21543 is LISTEN/ESTABLISHED, while bundled ADB reports 127.0.0.1:21543 offline. Physical Android remains absent from the latest canonical continuity state.

FAILED_AVOIDED: Prior start-server, disconnect/connect, polling and controlled MEmu backend restart did not recover transport. This round will not repeat those unchanged. The causal change is to verify and collapse competing local ADB daemon ownership to one bundled MEmu daemon, then reconnect the preserved running VM without clearing Kwai data or reinstalling anything.

SUCCESS_SIGNAL: bundled ADB reports 127.0.0.1:21543 as device and `adb -s 127.0.0.1:21543 shell getprop ro.product.model` returns successfully. After transport recovery, read-only Kwai identity/session probes may proceed; no publication is authorized by this lease.

FAILURE_SIGNAL: one-daemon reset completes but target remains offline, or the VM/forwarding disappears without automatic recovery.

TEST_VALIDITY: Anthares Remote command execution must remain healthy; MEmu_4 must remain running and 127.0.0.1:21543 must still be the configured forwarding target. Any unrelated Remote/control-plane regression invalidates the test rather than counting against the hypothesis.

SAFETY: preserve MEmu_4 user data and Kwai installation/session; no pm clear, uninstall, reinstall, account mutation or publication.