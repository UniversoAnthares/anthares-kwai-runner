# Anthares execution provider contract

GitHub remains the canonical repository and history source, but GitHub-hosted Actions runners are not the primary runtime compute path.

## Android / Kwai

Priority:

1. CircleCI — proven Android 35 machine executor with KVM.
2. Bitrise — Linux Android stack with AVD Manager; configured, live Android acceptance still required.
3. Firebase Test Lab — Spark no-cost Android device fallback for bounded automated validation. This lane is not interactive manual authentication.

Render is not an Android executor. GitLab shared runners are not Android executors because the available substrate exposes neither KVM nor Binder. Cirrus CI is retired and cannot be selected because the service shut down on 2026-06-01.

## Anthares-browser / runtime QA

Priority:

1. CircleCI.
2. Bitrise.
3. Render — tertiary browser/runtime-control fallback, not yet equivalent to the Dockerized 40-case CI proof.

GitHub Actions is manual diagnostic only while hosted-runner allocation is congested. GitLab is not in the active browser route while its CI quota is blocked.

## Failover

Before the publication boundary, if a provider fails readiness or cannot start within 90 seconds, select the next healthy/ready provider. A provider with no live status is not eligible. After a possible publication, never retry blindly on another provider; reconcile first.

## Invariants

- no PC dependency or fallback;
- no persistent local runner host;
- no secrets or authenticated session material in repository files;
- one active Kwai publication lease at a time;
- provider capability must match the role;
- retired providers cannot appear in active priorities;
- no-cost quota exhaustion fails closed rather than enabling billing.

Machine-readable source: `ci-hub/executor-routing.json`.
