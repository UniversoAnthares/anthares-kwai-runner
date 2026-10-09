# Remote cloud Chrome real Kwai website reachability
STATUS: PROVEN
AREA: kwai-codespaces-browser-webreach
DATE: 2026-10-09
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37939515944
RUN_INDEPENDENT: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37939532681
JOB: 113850000820
COMMIT: d9916f0723485625dff6a931d7556fa1652f7773
SUPERSEDES: test-hub/findings/20261009-lease-kwai-codespaces-webreach-1791553701.md
LEASE_CLOSED: test-hub/findings/20261009-lease-kwai-codespaces-webreach-1791553701.md

## Objective
Verify real www.kwai.com loading in a GitHub-hosted Chrome desktop rather than only a live CDP endpoint. No Android virtual or local PC executor, no credentials or cookies exported.

## Results
PROVEN: GitHub-hosted Debian Chrome connected through CDP to www.kwai.com over HTTPS, received HTTP 200, page title Make Everyone Shine and visible login controls. Browser-only security and fail-closed identity inspector remained healthy. Two independent workflow runs completed successfully. No account login, no identity verification and no persistence claimed.

## Decisive evidence
Run 37939515944 job 113850000820:
KWAI_CODESPACE_WEB_REACH={"origin":"https://www.kwai.com","http_status":200,"page_title":"Make Everyone Shine","login_controls_found":true,"authenticated":false,"credentials_used":false}
Run 37939532681 job 113850060296: same Kwai HTTP 200, title and login controls; KWAI_CODESPACE_IDENTITY_SMOKE={"inspector_connected":true,"identity_verified":false,"persistence_permitted":false,"chrome_survived":true,"credentials_used":false}.

## Consequence
No browser-network blocker remains in the tested GitHub-hosted Debian container. Next action requires account owner to create a private GitHub Codespace and authenticate through its GitHub-authenticated noVNC forwarded port 6080; then run identity check via private port 8765. The GitHub connector does not expose Codespaces list/create/status actions, so no Codespace creation or live login is asserted. Preserve previous security and synthetic crypto proofs. Do not export the browser profile to public repository or artifacts.
