# Cloudflare v12 production deploy blocked before mutation by multi-account selection
STATUS: FAILED
AREA: cloudflare
DATE: 2026-10-05
RUN: none
JOB: Wrangler OAuth production deploy
COMMIT: 48b7aef41385b63f94a8aa9e0948c3a8aa09efe9
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-2020-control-plane-final-snapshot-proven.md; test-hub/findings/20261005-2022-cloudflare-wrangler-dryrun-proven.md; test-hub/findings/20261005-2016-cloudflare-local-oauth-deploy-path-proven.md.
FAILED_AVOIDED: public runner without CLOUDFLARE_API_TOKEN and private-runner deploy paths were not reused. Source came from a fresh main clone and contained the v12 marker.
SUCCESS_SIGNAL: not reached.
FAILURE_SIGNAL: Wrangler exits before deploy because OAuth has multiple accounts and no account is selected.
TEST_VALIDITY: valid deployment harness failure before any Worker mutation. Wrangler explicitly exited with `More than one account available but unable to select one in non-interactive mode` and requested `account_id`/`CLOUDFLARE_ACCOUNT_ID`.

## Resultado
The fresh clone resolved to HEAD `48b7aef41385b63f94a8aa9e0948c3a8aa09efe9`. Wrangler OAuth was available, but production deploy stopped before upload because multiple Cloudflare accounts are attached to the session. The CLI listed the existing `anthares1` account and instructed the caller to select an account ID explicitly. No deploy occurred and no public verification was reached.

## Consequência
Do not repeat the same invocation. Under the still-active cloudflare-control lease, retry once with the OAuth-discovered `anthares1` account selected through `CLOUDFLARE_ACCOUNT_ID`, preserving the same fresh-source and public post-deploy acceptance checks. The account selector is configuration metadata, not a secret token.
