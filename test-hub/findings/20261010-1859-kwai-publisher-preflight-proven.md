# Kwai queue publisher preflight merged and observed in production workflow
STATUS: PROVEN
AREA: kwai-publish
DATE: 2026-10-10
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38077415448
JOB: control_preflight success, publish skipped
COMMIT: 4bad2ebb7fd6e821474bd3d7f576479419d703a0
SUPERSEDES: 20261010-1849-lease-kwai-publisher-preflight-merge.md

## Evidence
- PR #23 was squash-merged after CircleCI provider_smoke and kwai_install_smoke checks succeeded, bash preflight syntax validated, and mock /health tests returned ready=false for v12 and malformed JSON, ready=true only for exact v16 with required booleans.
- Deployed Cloudflare /health at 18:49Z returned no-pc-confirmation-v12.
- Post-merge run 38077415448 shows control_preflight completed success and publish completed skipped; no Android started, no video published.
- Public artifact upload no longer includes kwai-session.enc; encrypted session remains in private workflow cache, not public artifacts.

## Consequence
Preflight safety blocker closed. Real Kwai publication remains blocked by Cloudflare v16 deployment and authenticated Android identity. No repeat of 40-way QA or Android boot until prerequisites change. Kwai-publish lease closed.
