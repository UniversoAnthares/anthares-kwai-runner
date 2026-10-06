# TikTok rehydrate — alternate workflow_ref rejected by Cloudflare v12
STATUS: FAILED — causal isolation complete
AREA: tiktok-session
DATE: 2026-10-05
OWNER: CHAT 5

RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37394851557
WORKFLOW: `.github/workflows/tiktok-render-central-rehydrate.yml`
OBSERVED: the hosted runner executed normally, then the first GET to `/tiktok/session-state` returned HTTP 401 `{\"error\":\"unauthorized\"}`. No Render bootstrap or TikTok mutation was reached.
CONTROL: approved `.github/workflows/tiktok-central-session-read.yml` had returned HTTP 200 + available=true + 21 cookies minutes earlier against the same Cloudflare v12 production deployment.
CLASSIFICATION: Cloudflare v12 authorizes the approved workflow identity/workflow_ref rather than every workflow in the repository.
NEXT_CAUSAL_TEST: preserve the approved `tiktok-central-session-read.yml` path and extend that workflow after its successful central read to perform Render bootstrap, `/session-test`, identity verification, central refresh persist, and `/config-status`. Do not change Cloudflare control code.
SAFETY: zero publish calls; failure occurred before Render session mutation.
