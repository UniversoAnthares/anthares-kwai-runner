# ARA — operational handoff (2026-10-13)

## Verified

- GitLab project `87307279`, pipeline `2940582183`: **success** (Linux tests/race/vet and Windows amd64/arm64 cross-build).
- GitLab jobs used `k8s.saas-linux-small-amd64.runners-manager.gitlab.com/default` (Linux runner). Cross-compiling Windows executables **does not** validate Windows native behavior.
- GitHub PR #104 remains open at `feature/ara-capabilities`; its base is `feature/anthares-remote-agent`.
- ARA uses outbound HTTPS heartbeat, poll and result routes. Unit tests use an isolated TLS test server, not production infrastructure.

## Not verified / blockers

- CircleCI connected project and completed `ara_validation` run: **not verified**.
- AppVeyor connected project and native Windows test run: **not verified**.
- Failover GitLab -> CircleCI -> AppVeyor: **not implemented or demonstrated**. Config files alone do not implement failover.
- Production control plane authentication/authorization and device enrollment: **not verified**.
- Real Windows host end-to-end: **not verified**. Do not claim production readiness.
- The GitLab pipeline currently clones the mutable GitHub `feature/ara-capabilities` branch. A GitLab pipeline SHA refers to the GitLab CI config, **not** the exact tested GitHub commit. Record the checked-out GitHub commit SHA in every CI log/artifact before asserting provenance.

## Ownership boundaries

- Agent capabilities and Go security tests: this PR.
- Control plane and server deployment: coordinate with control-plane owner; use the documented `/v1/device/heartbeat`, `/v1/device/jobs/next`, and `/v1/device/jobs/{id}/result` contract.
- CI orchestration: implement independently of the device agent, with provider status polling, bounded deadlines, idempotency key per commit/test suite, provider priority and durable audit log. Never dispatch duplicate destructive jobs.
- Browser and social upload agents: do not change their workflows or application code from this PR.

## Acceptance criteria

1. Green native Windows AppVeyor job and direct job URL.
2. Green CircleCI job and direct URL.
3. GitLab, CircleCI, AppVeyor each demonstrably run independently of GitHub-hosted runners.
4. Failover integration test simulates primary timeout and secondary outage, proves one active attempt and recorded decision.
5. Production-like isolated control-plane test proves device auth, heartbeat, poll, result, and retry semantics.
6. Real Windows device enrollment requires separate explicit authorization; do not install software or touch the user's PC without permission.

No AI Commander, MeshCentral, local PC dependency, billing or card registration.
