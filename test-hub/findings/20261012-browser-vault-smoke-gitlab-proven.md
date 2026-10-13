# Anthares Browser Vault Smoke — external GitLab proof
STATUS: PROVEN
AREA: anthares-browser
DATE: 2026-10-12
PIPELINE: https://gitlab.com/universo-anthares-group/anthares-kwai-runner/-/pipelines/2940621837
JOB: 17126888892

## Result
The canonical GitHub `main` browser vault/runtime modules were cloned fresh inside an independent GitLab shared runner and the same smoke assertions as `.github/workflows/anthares-browser-vault-smoke.yml` completed successfully.

Decisive signal: `ANTHARES_BROWSER_VAULT_SMOKE=PASS`.

Queue time was ~0.09s and the job completed in ~34.6s. The GitHub copies of this smoke remaining queued are therefore an executor-allocation issue, not evidence of a browser-vault code failure.

## Proven boundaries
- production entrypoint selects `anthares_runtime_mesh_vaulted`;
- P-256 signing public key is exposed;
- local vault encryption/decryption round-trip succeeds;
- hybrid adapter reports the vault backend healthy;
- `/v1/runtime/browser/signing-public-key` responds successfully;
- `/v1/runtime/health` reports `local_playwright_vault` and `host_desktop_fallback=false`.

## Rule
Do not repeat the same static vault smoke on GitHub-hosted runners merely because their queued copies have not started. Continue with live runtime/session acceptance separately.
