# Git provider failover — Codeberg suspended

Operational routing as verified on 2026-10-28. GitHub remains the canonical
write authority. Codeberg is **not** an eligible automatic mirror, CI executor,
publisher, or failover destination while the account is suspended.

## Current verified routes

- **GitHub → Forgejo:** the independent Windows job
  `Anthares Forgejo Git Redundancy 30min` verifies all source refs for its
  15 allowlisted repositories. The GitHub workflow
  `.github/workflows/forgejo-mirror-sync.yml` provides an additional
  scheduled check, but GitHub cron delivery is not a guaranteed 10-minute SLA.
- **GitHub → GitLab:** the Windows task `CORTES-Git-Provider-Mirrors`
  targets only GitLab. Its recorded `PROVEN_SUPERSET` result means the
  GitHub main commit is an ancestor of the GitLab main commit; it does
  **not** establish exact head equality, full-ref parity, or permission
  to reset the GitLab branch. GitLab hosted CI remains ineligible when
  `ci_quota_exceeded` persists.
- **GitLab → Forgejo:** `Anthares Forgejo GitLab Extra Mirrors 30min`
  verifies three extra public source sets. Other independent GitLab
  histories are tracked separately; do not treat these extra mirrors as
  evidence that all six independent histories have been imported.
- **Codeberg:** `.github/workflows/mirror-codeberg.yml`,
  `.github/workflows/x-codeberg-neon-promote.yml` and
  `.github/workflows/cortes-tiktok-codeberg-guarded-promotion.yml`
  are intentionally disabled. The legacy Windows Codeberg Clipper
  mirror and Codeberg TikTok watchdog are disabled.

## Selection and safety

NORMAL: use GitHub as canonical source, with Forgejo and GitLab as
independent, verified backups. Never take Codeberg as primary or attempt
to restore Codeberg publishing because a stale URL or workflow exists.

GITHUB_UNAVAILABLE: independently confirm the intended Git ref, commit
and tree on Forgejo, then on GitLab if needed. Promote neither a stale
nor a divergent replica automatically. Require fresh integrity,
appropriate authorization and an explicitly validated recovery plan.

CI: use a provider only after current real runner eligibility, secret
availability, quota and job results are verified. A Git mirror does not
itself establish a working CI runner. Do not assume the Hostinger
read-only Forgejo runner can execute Linux browser or publishing jobs.

PUBLICATIONS: GitHub's TikTok jobs are guarded against simultaneous
Forgejo-primary publication. X has a separate GitHub workflow gated by
`ANTHARES_X_AUTOPUBLISH`. Do not arm X, Clipper or TikTok on an
unhomologated provider. Keep Neon idempotency, fencing, daily limits
and reconciliation of uncertain publication outcomes.

RECOVERY: compare source and destination branches, tags and reachable
objects. Never force-push, reset shared branches, overwrite unrelated
histories or recreate blocked operations through another route. The
Codeberg-exclusive public histories were recovered separately to
private external storage, not merged into production Git branches.

## Historical note

The 2026-10-21 Codeberg-preferred mirror strategy and its pre-suspension
SHA and Actions findings are obsolete. Do not use them as operational
selection criteria after the 2026-10-27 account suspension.
