# Private cloud Chrome desktop and fail-closed identity inspector
STATUS: PROVEN
AREA: kwai-codespaces-browser
DATE: 2026-10-09
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37938604983
JOB: 113846903755
COMMIT: 17be4e57267ec428942ffecd0760d5f8beff910d
SUPERSEDES: test-hub/findings/20261009-lease-kwai-codespaces-browser-1791552928.md
LEASE_CLOSED: test-hub/findings/20261009-lease-kwai-codespaces-browser-1791552928.md

## Objective
Prepare an interactive Chrome desktop hosted in GitHub Codespaces with GitHub-authenticated private ports, no Android virtual, no user-PC executor, and an identity verifier that never claims authentication from a hidden login button.

## Results
PROVEN in GitHub-hosted Debian container equivalent to the Codespaces devcontainer: Chromium, Xvfb, Openbox, x11vnc, noVNC and identity guard all installed and started. Local loopback noVNC 6080, guard 8765, Chrome CDP 9222 and VNC 5900 responded. The guard connected to actual Chrome, returned identity_verified=false and persistence_permitted=false for an unauthenticated browser, and Chrome remained alive after inspection.

The first integration run 37938233842 FAILED at apt-get update due an unrelated upstream Yarn APT source with missing signing key. The fix disables only that unused source without relaxing signature checks. Retest 37938369293 PROVEN for desktop boot, then 37938604983 PROVEN for actual guard-to-Chrome inspection.

## Decisive evidence
Run 37938604983 job 113846903755:
KWAI_CODESPACE_DESKTOP_SMOKE={"novnc":true,"guard":true,"chrome_cdp":true,"vnc_loopback":true,"identity_verified":false,"android_used":false,"credentials_used":false,"synthetic_only":true}
KWAI_CODESPACE_IDENTITY_SMOKE={"inspector_connected":true,"identity_verified":false,"persistence_permitted":false,"chrome_survived":true,"credentials_used":false}
Security QA run 37938175969: Ran 8 tests; OK. Follow-up security QA run 37938585862: success.

## Consequence and limits
The repository contains .devcontainer/devcontainer.json, kwai-install.sh, kwai-start.sh, kwai-identity-guard.py, kwai-clear-session.sh, tests and docs. GitHub Codespaces private forwarded ports are authenticated by GitHub by default; the user must keep 6080 and 8765 visibility PRIVATE. Browser profile stays in the Codespace's private HOME, not in Git, and is not automatically exported.

IMPORTANT: No actual Codespace has been provisioned by this agent, and NO Kwai account has been authenticated or server-identity-verified. The hosted synthetic/unauthenticated smoke is not a real login. Account owner must create their Codespace using https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=1406232047 and perform login through the private forwarded browser. Only then can the inspector evaluate owner-specific controls. Preserve previous browser-only probe #37936848163 and synthetic cross-run crypto #37935784822; do not use Android virtual or local PC.
