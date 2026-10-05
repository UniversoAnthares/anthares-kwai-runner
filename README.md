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
