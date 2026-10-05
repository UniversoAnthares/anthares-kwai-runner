# Anthares Kwai Runner

Public, disposable Android runner for the Universo Anthares Kwai publishing pipeline.

This repository contains only generic runner infrastructure. Account credentials, private controller URLs, private application logic and publishing policy remain outside the repository.

Required GitHub Actions secrets:
- KWAI_LOGIN
- KWAI_PASSWORD
- ANTHARES_CONTROL_URL
- ANTHARES_CONTROL_TOKEN

The runner installs only a previously validated Kwai package supplied as a workflow artifact or release asset.
