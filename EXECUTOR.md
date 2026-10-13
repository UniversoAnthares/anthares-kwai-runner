# Anthares Android Executor Contract

The Android executor is disposable cloud compute created only when a job exists.

## Active provider order

GitHub Actions hosted runners are retired from the Android execution path. GitHub remains the canonical repository and run-history source, not Android compute.

Android/Kwai execution priority:

1. CircleCI — primary. Android 35 machine executor with KVM; already proven in the project.
2. Bitrise — secondary. Linux Android stack with AVD Manager; configured and awaiting live acceptance proof.
3. Firebase Test Lab — tertiary. Spark no-cost Android device execution for bounded automated validation/fallback; it is not the interactive manual-auth lane.

Browser/runtime QA priority:

1. CircleCI.
2. GitLab shared Linux runner.
3. Bitrise.

Cirrus CI is retired and must never be selected: the service shut down on 2026-06-01. GitLab is intentionally excluded from Android emulation because its shared runner substrate does not expose KVM or Binder.

Failover rule: if a provider cannot start within 90 seconds or fails before the readiness gate, move to the next eligible provider. A publication that crossed the publication boundary is never retried blindly; it enters reconciliation first.

## Lifecycle

1. controller requests a job;
2. routing selects the first healthy/ready provider with queue delay <= 90 seconds;
3. provider provisions disposable compute/device capacity;
4. Android API 35 or the provider device boots;
5. the validated Kwai vault is checksum-verified and installed;
6. job automation runs;
7. result/evidence is returned;
8. disposable capacity is destroyed.

## Operational invariants

- no PC dependency or fallback;
- no persistent local runner host;
- no credentials or sessions in repository files;
- one active Kwai publication lease at a time;
- retries are idempotent before publication boundary;
- possible publication always reconciles before retry;
- GitHub Actions hosted runners are not eligible for Android execution;
- a provider absent from live status is not eligible;
- retired providers cannot appear in an active priority list.

Machine-readable routing source: `ci-hub/executor-routing.json`.
