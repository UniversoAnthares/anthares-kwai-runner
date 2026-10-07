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

CircleCI is configured through `.circleci/config.yml` with the shared provider smoke job. GitHub remains the source of truth; CircleCI is an interchangeable external executor.


## Neutral dual-provider execution

GitHub and GitLab are treated as peer execution providers. The provider-router state machine in `tools/provider_router.py` enforces single-writer leases, checkpoint fencing and quota/down failover. The contract is documented in `tools/DUAL_PROVIDER_ARCHITECTURE.md`. Durable lease/checkpoint persistence remains in the existing `anthares-control`; no second controller is introduced.
