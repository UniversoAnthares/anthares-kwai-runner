# Anthares execution provider contract

GitHub remains the canonical repository and history source. General CI uses GitHub Actions as the primary hosted executor, with independently verified fallbacks.

## General CI

Priority:

1. GitHub Actions — primary general CI.
2. Harness — verified hosted Linux CI with automatic push trigger.
3. AppVeyor — verified hosted Windows build/test and artifact upload.
4. Floot — verified remote Node execution and PHP 8.4 via php-wasm.
5. Cloudflare Workers Builds — verified Git-connected build/deploy.
6. GitLab CI — last-resort hosted Linux fallback; currently quota-blocked.

CircleCI is retired and must not be selected by active routing.

## Android / Kwai

Priority:

1. Physical Android device — primary authenticated device path.
2. MEmu Android — standby fallback only after primary-device failure.
3. GitHub Actions — remote Android secondary; live acceptance still required for the current replacement path.
4. Bitrise — Linux Android stack; live runtime proof still required.
5. Firebase Test Lab — bounded noninteractive Android fallback.

Render is not an Android executor. CircleCI and Cirrus CI are retired.

## Anthares-browser / runtime QA

Priority:

1. Cloudflare Browser Rendering + Durable Objects — active proven browser runtime.
2. Bitrise — configured standby; not eligible until a live browser QA proof passes.
3. GitLab CI — configured standby but currently blocked by `ci_quota_exceeded`.
4. Render — final legacy fallback only while retirement/migration is unfinished.

GitHub Actions is not the default browser executor. Cloudflare is the only currently proven active browser path that is independent of the local PC and Render.

## Failover

Before the publication boundary, if a provider fails readiness or cannot start within 90 seconds, select the next healthy/ready provider. A provider with no live status is not eligible. After a possible publication, never retry blindly on another provider; reconcile first.

## Invariants

- no PC dependency or fallback for hosted CI;
- no persistent local runner host for hosted CI;
- no secrets or authenticated session material in repository files;
- one active Kwai publication lease at a time;
- provider capability must match the role;
- retired providers cannot appear in active priorities;
- no-cost quota exhaustion fails closed rather than enabling billing;
- recovery verification must not redeploy a competing Worker entrypoint.

Machine-readable source: `ci-hub/executor-routing.json`.
