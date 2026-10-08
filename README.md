# Shared operational state

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

## External CI provider smoke

CircleCI is configured through `.circleci/config.yml` with the shared provider smoke job. CircleCI is an interchangeable external executor; it is not a repository authority.

## Neutral dual-provider execution

GitHub and GitLab are peer execution providers. Neither provider is permanently authoritative. The provider-router state machine in `tools/provider_router.py` enforces single-writer leases, exact-HEAD fencing on the active provider, and quota/down failover. Cross-provider failover accepts either the exact checkpoint commit or an explicit verified `content_id` (for example the Git tree SHA), allowing byte-equivalent repositories with independently created commits to remain usable without treating different commit IDs as content divergence.

The contract is documented in `tools/DUAL_PROVIDER_ARCHITECTURE.md`. Durable lease/checkpoint persistence remains in the existing `anthares-control`; no second controller is introduced. All mutations must follow the fresh read, lease, peer check and optimistic-concurrency sequence in `AGENTS.md`.
