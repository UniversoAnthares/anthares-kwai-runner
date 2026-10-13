# Anthares Android Executor Contract

The Android executor is a disposable cloud VM created only when a job exists.

## Provider order

GitHub Actions hosted runners are retired from the Android execution path. GitHub remains the canonical repository and run-history source, not the Android compute provider.

Android/Kwai execution priority is:

1. CircleCI — primary. Proven Android 35 machine executor with nested virtualization/KVM.
2. Cirrus CI — secondary. KVM-enabled Android SDK container.
3. Bitrise — tertiary. Linux Android stack with AVD Manager.

Failover rule: if a provider cannot start within 90 seconds or the executor fails before the Android/Kwai readiness gate, move to the next provider. A publication that crossed the publication boundary is never retried blindly; it must enter reconciliation first.

GitLab shared runners are coordination/generic CI only. They are not Android executors because the shared runner substrate does not expose KVM or Binder.

## Lifecycle

1. controller requests a job;
2. routing selects CircleCI, then Cirrus, then Bitrise;
3. provider provisions a disposable Android-capable runner;
4. workflow boots Android API 35 with hardware acceleration;
5. validated Kwai vault is downloaded and checksum-verified;
6. job automation runs;
7. result/evidence is returned;
8. VM is destroyed.

## Operational invariants

- no PC dependency;
- no persistent local runner host;
- no credentials in repository files;
- no private repository dependency;
- one active Kwai publication lease at a time;
- retries must be idempotent;
- visual tunnel is diagnostic/authentication only;
- GitHub Actions hosted runners are not eligible for Android execution;
- provider health and queue delay determine failover;
- after a possible publication, reconciliation is mandatory before another provider may retry.

Provider routing machine-readable source: `ci-hub/executor-routing.json`.
