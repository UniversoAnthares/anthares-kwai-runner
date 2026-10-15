# Lease — Kwai login / ADB server port repair

STATUS: RUNNING
AREA: kwai-login|android|session
DATE: 2026-10-15
RUN: none
JOB: Anthares Remote jobs 47ef4ebca8a53c3e985942ae54f3c82e, c7a24b1d258fc6058257cdfc50fcc47c
COMMIT: pending
SUPERSEDES: none
LEASE_OWNER: chatgpt-20261015-1924
LEASE_EXPIRES_LOCAL: 2026-10-15T19:54:00-04:00

BASELINE_PROVEN: Anthares Remote is connected through backend vercel-neon and remote_exec roundtrip returned ARA_ROUNDTRIP_OK under NT AUTHORITY\SYSTEM. MEmu_4 backend is running and host forwarding 127.0.0.1:21543 is listening.

FAILED_AVOIDED: the previous recovery ladder repeatedly used the default ADB server on port 5037 and observed 127.0.0.1:21543 offline. This lease does not repeat that path unchanged. New causal evidence shows two ADB servers: SYSTEM port 5037 reports MEmu offline, while the existing interactive-session server on port 5038 reports the exact same MEmu transport as device (SM-S938B).

SUCCESS_SIGNAL: Anthares Android Runtime uses an explicit/configurable ADB server port, health/select sees MEmu transport=device with boot_completed=true and Kwai package installed, without clearing app data or publishing content.

FAILURE_SIGNAL: runtime using the proven 5038 server still reports offline/missing, or the guest fails boot/package probes.

TEST_VALIDITY: direct `adb -P 5038 devices -l` must continue to show 127.0.0.1:21543 device during the runtime validation; if that baseline changes, the mutation test is invalid rather than FAILED.

No publication is authorized by this lease. F17 requires exact identity @lucasrosalem and persistence after controlled restart without publishing.
