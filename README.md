# Shared operational state

**Mandatory video policy (2026-10-13):** Before any clip generation, upload, publication, or E2E test, read the canonical platform duration, shared-master and per-account daily quotas in [`UniversoAnthares/anthares-clipper/README.md`](https://github.com/UniversoAnthares/anthares-clipper/blob/main/README.md), section **Política obrigatória de distribuição**. Old durations and quotas are superseded. Keep independent queue, ledger, retry and confirmation for every `platform + account_id`. The policy is normative; do not claim runtime migrated without code verification.


**Before running or changing any Anthares automation test, read [test-hub/README.md](test-hub/README.md) and [AGENTS.md](AGENTS.md). The append-only evidence ledger is [test-hub/findings/](test-hub/findings/).**

# Anthares Kwai Runner

Public, disposable Android runner for the Universo Anthares Kwai publishing pipeline.

This repository contains only generic runner infrastructure. Account credentials, private controller URLs, private application logic and publishing policy remain outside the repository.

Required now:
- KWAI_LOGIN
- KWAI_PASSWORD

Reserved for the later controller-integration stage (not required by the current Android acceptance path):
- ANTHARES_CONTROL_URL
- ANTHARES_CONTROL_TOKEN

The runner downloads the validated Kwai package from this repository's public `kwai-package-vault` release and verifies its pinned SHA-256 before installation. No private-repository token is required.

## External CI providers

General CI priority is defined in `ci-hub/executor-routing.json`: GitHub Actions (when runners are assigned), AppVeyor (when a current job starts), Harness, Floot, Cloudflare Workers Builds, and a future Codeberg Actions runner **only after live authorization and execution proof**. GitLab hosted CI is excluded while quota-blocked; its independent authenticated Issues transport remains available for Anthares Remote recovery. Codeberg Git is the preferred independent **source mirror**, subject to a fresh exact SHA match before promotion; it is not itself an executor. CircleCI remains retired.

## Neutral multi-provider execution

GitHub remains the canonical repository/history source, while execution can fail over across the active provider chain. The provider-router state machine in `tools/provider_router.py` enforces single-writer leases, exact-HEAD fencing on the active provider, and quota/down failover. Cross-provider failover accepts either the exact checkpoint commit or an explicit verified `content_id` (for example the Git tree SHA), allowing byte-equivalent mirrors with independently created commits to remain usable without treating different commit IDs as content divergence.

The contract is documented in `tools/DUAL_PROVIDER_ARCHITECTURE.md`. Durable lease/checkpoint persistence remains in the existing `anthares-control`; no second controller is introduced. All mutations must follow the fresh read, lease, peer check and optimistic-concurrency sequence in `AGENTS.md`.
