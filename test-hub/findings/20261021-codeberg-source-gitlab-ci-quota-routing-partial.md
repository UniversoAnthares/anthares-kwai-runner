# Codeberg priority source failover; GitLab CI quota exclusion
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-21
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39665507700
JOB: 119449385764
COMMIT: pending merge
SUPERSEDES: none

## BASELINE_PROVEN
The Codeberg repo https://codeberg.org/UniversoAnthares/anthares-kwai-runner is publicly readable, and its main commit 1c2f7dc3341c was 20 ancestors behind GitHub 2884ff77c425 at the read-only sample, with no divergence. An earlier Codeberg mirror (GitHub run 39665507700) successfully pushed main at that SHA and proved that Codeberg credentials are stored in the authorized GitHub Actions secret store. Do not duplicate or exfiltrate them. Codeberg API returned has_actions=false, default_branch=fix/queue-claim-shell-env-injection-20261010. Local unattended git push dry-run found no Codeberg write authorization (no manual credential prompt allowed).
GitLab CI pipeline 2973638637 reports failure_reason=ci_quota_exceeded, including jobs never assigned a runner. AppVeyor primary/duplicate projects showed builds 54927735 and 54927736 queued since October 19. Github mirror run backlog includes many canceled/stale jobs.

## FAILED_AVOIDED
No force-push, no override of Codeberg main, no assertion that repository mirroring enables hosted CI or personal OAuth publishing. No change to independently PROVEN GitLab private issue recovery transport for Anthares Remote.

## SUCCESS_SIGNAL
A new GitHub main mirror run executes, shows CODEBERG_MAIN_FAST_FORWARD_VERIFIED=PASS, and independent git ls-remote reports equal Codeberg/GitHub main hashes; routing test passes and GitLab CI is excluded.

## FAILURE_SIGNAL
Missing secret, Codeberg divergent history, CI runner never allocated, mismatch after push, or Codeberg Actions still disabled. Such a case must not be promoted to operational redundancy.

## TEST_VALIDITY
Codeberg source promotion remains BLOCKED until actual matching SHA proof. CI migration remains PARTIAL; no Codeberg runner was provisioned or proven. The ready-to-run mirror is not the same as a successful sync.

## Result
Updated verified mirror workflow to main-only, coalesced queue, scheduled retries and fail-closed credential/ancestry/post-push SHA verification. Machine CI routing excludes GitLab CI, models Codeberg Actions as unavailable and Codeberg source as stale. Preserve the real Anthares Remote recovery queue until a separately proven replacement is available.
