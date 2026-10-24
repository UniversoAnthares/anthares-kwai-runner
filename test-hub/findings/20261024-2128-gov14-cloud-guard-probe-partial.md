# GOV-14: cloud guard capability probe result (no deployment)
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-24
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40134278061
JOB: R076-GOV14-20261024
COMMIT: anthares-clipper 2084019a95cfa04560866bb3a18722e92344771f
SUPERSEDES: 20261024-2118-gov14-cloud-guard-lease-chatgpt.md
OWNER: chatgpt-gov14
SCOPE: cloud capability diagnostic, no deploy, secrets, queue, publisher or OS-ACL modifications

## Preflight
- Governance preflight on D:\AntharesWork\anthares-clipper and D:\AntharesWork\anthares-kwai-runner: f6fc9ca59a96e451.
- Governance audit 218 repositories, zero failures.
- Original Windows worktrees were preserved (existing dirty changes not reset).
- Peer GitLab main did not contain the exact .github/workflows/network-scope-guard.yml at the queried historical head; no blind mirroring.

## Change and real evidence
- Test Hub lease PR https://github.com/UniversoAnthares/anthares-kwai-runner/pull/1326 merged as 8a88a607bf21afa86d8f83b84360e21265bcb97e.
- Platform-only probe PR https://github.com/UniversoAnthares/anthares-clipper/pull/196 merged as 2084019a95cfa04560866bb3a18722e92344771f. New file is .github/workflows/network-scope-cloud-probe.yml, push-on-file-change/manual-only, read-only, Ubuntu 24.04, no publisher secrets or deploy, 23 previously-authorized scope tests only.
- Existing trusted-base guard on PR #196: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40134193308 completed SUCCESS. Ownership/rename validation and approved contract tests succeeded.
- New GitHub-hosted capability run 40134278061 auto-triggered after merge, completed FAILURE **before recording any job steps**. GitHub job 120992361408 was FAILED with steps=[]; attempt to read its logs returned 404 BlobNotFound. Root cause unverified (runner allocation/billing/quota is a possible hypothesis, not a proven diagnosis).
- Important: this result is NOT a rejection of scope-guard code because the test runner did not execute tests; no retry until causal condition is established.
- Existing .github/workflows/network-scope-guard.yml remains unchanged, on its previously functioning self-hosted runner. Hosted probe does not replace it and grants no deployment rights.

## GOV-14 remaining acceptance gates
1. Independently permissioned release controller must be the ONLY holder of deployment capability. Network-agent identities must not push to protected base, change release policy or redeploy another network.
2. Required branch/merge checks must actually reject a violating actor, rather than relying on a voluntary GitHub Action. GitHub private branch protection and repository rulesets returned 403 in earlier verified audits; GitLab protected=true together with can_push=true for connected account does not satisfy negative proof.
3. Trusted governance hash, base SHA, owner/job, PR changed paths, reviewer/release approval, exact artifact digest, rollout and rollback must be bound to every promoted release.
4. Complete practical cross-network negative checks with real separately scoped identities using authorized mechanisms. Previously security-denied tests are NOT repeated by changing tool/runner.
5. Prove eligible cloud runner, then select it as primary and Windows personal executor LAST. Do not promote an allocation-failed probe.

## Status decision
GOV-14 remains PARCIAL. Partial proof: authoritative preflight and audit, trusted-base ownership check with real CI success, and an independently versioned cloud-capability probe that failed before executing. Global structural enforcement is NOT complete. No production publisher, secrets, SQL, queue or existing guard changed.
