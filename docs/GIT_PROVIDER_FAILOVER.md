# Git provider failover — Codeberg preferred peer

As of 2026-10-21, GitHub is the canonical write authority. Codeberg is the
preferred **source mirror** for recovery, with strict fresh-content checks.
GitLab hosted CI is excluded because real pipeline jobs fail with
`ci_quota_exceeded`. The previously proven private GitLab issue queue for
Anthares Remote stays active until a separately proven transport replaces it;
that API is independent of GitLab CI minutes.

## Verified state (21 October 2026)

- GitHub main: `2884ff77c425` at the sampled comparison (moves frequently).
- Codeberg main: `1c2f7dc3341c`, 20 commits behind at the sampled comparison.
  Codeberg commit was a direct ancestor, so fast-forward is safe. **Not promoted.**
- Last Codeberg mirror job proven to update the public ref:
  GitHub Actions run `39665507700`. The authenticated secret
  `CODEBERG_PUSH_URL` already exists on that runner; never copy or print it.
- Codeberg API shows `has_actions=false` and default branch
  `fix/queue-claim-shell-env-injection-20261010`, **not** `main`.
  An authenticated repository administrator must enable Actions and correct the
  default branch after verifying the intended protected-branch policy.
- GitLab hosted CI reports `ci_quota_exceeded` in pipeline `2973638637`.
- AppVeyor mirror project builds `54927735` and `54927736` were queued,
  without a currently proven hosted runner. Do not equate historical success
  with present-day capacity.

## Safe synchronization

Workflow `.github/workflows/mirror-codeberg.yml` now only mirrors
`main`, serializes and coalesces frequent pushes, and runs periodically.
It fails closed if the existing Codeberg push secret is missing. For every run:

1. Fetch the latest authoritative GitHub main.
2. Fetch the current public Codeberg main without privileged credentials.
3. Verify Codeberg head is an ancestor of GitHub head, otherwise stop.
4. Push exactly `main` **without force** using the preexisting GitHub secret.
5. Independently read back public Codeberg main and compare full SHAs.

A queued/pending/canceled workflow or a green result without
`CODEBERG_MAIN_FAST_FORWARD_VERIFIED=PASS` does **not** count as synchronization.
The source mirror is eligible for failover only after fresh SHA parity.

## Selection rules

NORMAL: Github is canonical. Codeberg is a checked independent repository backup.

GITHUB_UNAVAILABLE: consider Codeberg first **only** after a new independent
read confirms correct SHA/branch/tree, absence of divergence and the intended
checkpoint. If Codeberg is stale, fail closed and inspect the verified GitLab
repository in an explicitly authorized emergency recovery; never silently
deploy old Codeberg code.

CI: GitLab CI is removed from automatic routing. AppVeyor and Github public
Actions are candidates only when a recent real job proves an available runner.
Codeberg Actions is **not** an executor while `has_actions=false`; merely
hosting a Git mirror does not create a worker or authorize personal LinkedIn
OAuth and Neon OIDC. Enabling Actions, establishing runner eligibility, and
independently validating signed publisher authorization are explicit gates.

PUBLICATIONS: the Neon central ledger/fencing, 100/day ceiling across social
networks and account-level limits remain authoritative. Never run simultaneous
GitHub and Codeberg publishers before proving idempotence and mutually
exclusive leases; reconcile uncertain posts before re-execution.

RECOVERY: compare every reachable provider's intended branch and tag refs.
Never automatically force-push, hard-reset a shared branch, rewrite divergent
history, or promote stale content. All credentials stay in authorized
provider/CI secret stores.
