# TikTok 15-environment replacement — invalid at OIDC boundary
STATUS: PARTIAL
AREA: tiktok-publish
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37451475451
SUPERSEDES: test-hub/findings/20261006-0645-lease-tiktok-15env-replacement.md

All 15 environment jobs failed before browser/session testing with HTTP 401 from the protected central-session endpoint. This does not refute any browser environment. The new workflow_ref was outside the deployed OIDC allowlist.

Causal correction: reuse the already allowlisted canonical tiktok-real-publish workflow, currently configured as a read-only 15-replica account/API matrix. No publication_started or irreversible publish occurs in that matrix. Do not repeat the unallowlisted workflow unchanged.
