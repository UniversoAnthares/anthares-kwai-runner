# GitLab OIDC Worker deployed, unauthorized rejected
STATUS: PARTIAL
AREA: cloudflare
DATE: 2026-10-08
RUN: https://anthares-control.anthares1.workers.dev
JOB: none
COMMIT: 14df310d7b1b698337b9f525e6bee0dc6883b6df
SUPERSEDES: 20261008-cloudflare-runtime-secrets-first-deploy-partial.md

## Resultado
GitLab JWT RS256 signature verification against gitlab.com OIDC JWKS added to Cloudflare runtime-secrets module. Requires project_id 87361774, project_path UniversoAnthares/anthares-clipper, protected main branch, expected audience, accepted pipeline sources, and explicit scope clipper-publish. GitHub OIDC path retained. Deployed Wrangler version 846a55ec-3a8c-45df-b587-2403028e1779.

## Evidência
Wrangler deployment successful. Node unauthenticated POST to /runtime-secrets returned HTTP 401.

## Limitations
No real GitLab id_token acceptance test yet. No six operational secrets provisioned. GitLab CI consumer not wired. No end-to-end publish failover. Do not claim production-ready. Existing Worker accepts GitHub OIDC claims from previously allowlisted workflows; further review of exact least-privilege identity is required. Verify GitLab ref_protected claim type against actual token before acceptance test. No credentials in this finding.

## Next
Implement GitLab CI job with id_tokens audience, protected branch, fetch response without logging, and integration tests 401/403/503/200 with mock secrets only. Securely provision six secrets via authorized source, not GitHub Actions secret readback. Prove GitLab hosted publishing with independent publication confirmation.
