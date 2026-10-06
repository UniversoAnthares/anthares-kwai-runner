# Cloudflare control OIDC deploy — blocked by missing Actions secret
STATUS: BLOCKED
AREA: cloudflare
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37411521388
JOB: 112100789901
COMMIT: 7e571d076adbc0fa48cf86d6294fea588012baff
SUPERSEDES: test-hub/findings/20261006-lease-cloudflare-control-tiktok-oidc-deploy.md

## Objetivo
Deploy the repository Cloudflare control snapshot containing the already-reviewed `tiktok-reconcile-v2.yml` OIDC allowlist entry.

## Resultado
The deployment workflow reached the exact deploy step. Snapshot validation passed with `SNAPSHOT_VALID=queue-fencing-v16`. Deployment stopped before Wrangler because `CLOUDFLARE_API_TOKEN` is empty in GitHub Actions. No Cloudflare mutation occurred.

## Evidência decisiva
Run 37411521388 / job 112100789901:
- SNAPSHOT_VALID=queue-fencing-v16
- environment showed `CLOUDFLARE_API_TOKEN:` empty
- job exited 1 at `test -n "$CLOUDFLARE_API_TOKEN"`

The repository source already contains `tiktok-reconcile-v2.yml` in the OIDC allowlist. The currently deployed control plane therefore remains older than the repository snapshot.

## Consequência
Do not repeat the deploy workflow unchanged. A Cloudflare API token must become available to the existing deployment workflow, or an already-authorized Wrangler OAuth deployment path must be used. Once deployed, rerun the read-only TikTok reconciliation probe before any publication attempt. This finding closes the lease and records the exact external blocker.