# Cloudflare control plane v12 is deployed and production-proven
STATUS: PROVEN
AREA: cloudflare
DATE: 2026-10-05
RUN: none
JOB: Wrangler OAuth production deploy + public structural acceptance
COMMIT: 1addd59be378425258cf476cf901248c825148c2
SUPERSEDES: test-hub/findings/20261005-2008-cloudflare-production-stale-local-fallback.md

BASELINE_PROVEN: test-hub/findings/20261005-2020-control-plane-final-snapshot-proven.md; test-hub/findings/20261005-2022-cloudflare-wrangler-dryrun-proven.md; test-hub/findings/20261005-2016-cloudflare-local-oauth-deploy-path-proven.md.
FAILED_AVOIDED: public-runner missing-secret and private-runner deployment paths were not reused. The first OAuth production invocation was stopped before mutation by multi-account selection and is recorded separately; the retry selected the already-discovered anthares1 account explicitly.
SUCCESS_SIGNAL: production deploy completes; public /health reports version `2026-10-05-no-pc-confirmation-v12` and pc_fallback=false; /strategy has no exact local/pc executor; /failover-self-test has no local/pc executor and reports local_retired=true.
FAILURE_SIGNAL: stale version, pc_fallback enabled, or local/pc executor remains reachable.
TEST_VALIDITY: deployment used a fresh clone of current main under the active cloudflare-control lease. Acceptance queried the public workers.dev endpoint after deployment, not local source.

## Resultado
PROVEN in production. Wrangler uploaded and deployed `anthares-control`; Cloudflare reported Version ID `960c9ae5-e3fc-4e9f-b662-7a28dc8b6c6b`. Public `/health` returned version `2026-10-05-no-pc-confirmation-v12`, persistent_state=true, queue_bound=true and pc_fallback=false. Public `/strategy` returned cuts=[render,github], tiktok=[render,github], kwai=[github], kwai_live=[hls_origin,github], control=[cloudflare,github,render], oracle=false and google_compute=false. Public `/failover-self-test` returned render -> github -> null, local_retired=true, priority=[render,github]. Structural acceptance emitted `CLOUDFLARE_V12_PUBLIC_STRUCTURAL_ACCEPTANCE_OK`.

The deployment command itself completed successfully. An initial post-deploy regex check produced a false positive because the strategy label contains `no-pc`; a second structural verification checked exact JSON executor values and passed. Production state therefore reflects the new v12 Worker.

## Consequência
The stale-production blocker is closed. The v12 GitHub OIDC allowlist and fail-closed queue lifecycle are now usable by approved workflows, including the prepared Kwai `/github-queue/started`/complete/fail adapter. Consumers must continue checking the explicit production version when safety depends on these invariants. This result closes the cloudflare-control lease opened in `20261005-2112-lease-cloudflare-control-v12-production-deploy.md`.
