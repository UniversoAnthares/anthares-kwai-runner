# ARA GitHub Actions control-plane migration lease

STATUS: RUNNING
AREA: ara-admin-control-transport
OWNER: chatgpt-ara-github-actions-migration
LEASE_START_UTC: 2026-10-13T15:53:00Z
LEASE_EXPIRES_UTC: 2026-10-13T16:25:00Z

BASELINE_PROVEN:
- The current ChatGPT Anthares Remote connector still reports `control_origin=https://anthares-ara-control.onrender.com` and `connected=false`.
- The user explicitly requires Anthares Remote to stop depending on Render, and reports the Cloudflare quota exhausted.
- `UniversoAnthares/anthares-ara-queue` exists and is private.
- Main already contains GitHub/GitLab issue-queue transport code, but activation still depends on a persistent private-repository credential on Windows.
- A repository self-hosted GitHub Actions runner has existed for Anthares administration; this lease tests that independent transport without using Render or Cloudflare.

FAILED_AVOIDED:
- Do not make Cloudflare a required runtime or failover while its quota is exhausted.
- Do not return to Render as the canonical Anthares Remote control plane.
- Do not expose tokens, private queue payloads, or arbitrary shell commands in public workflow inputs.
- Do not touch the concurrent `issue_queue.go` implementation while another agent is changing/testing it.

SUCCESS_SIGNAL:
- A `runs-on: self-hosted` diagnostic executes on the Anthares Windows runner without Render/Cloudflare and returns a non-secret capability report.
- If that succeeds, use this channel to install the validated agent/bridge and verify a safe `ping` round trip before disabling the obsolete Render-connected path.

FAILURE_SIGNAL:
- The self-hosted workflow remains queued/offline, or no secure persistent credential exists for the private issue queue.

TEST_VALIDITY:
- Diagnostic must not print credentials and must not open interactive Windows UI.
- No social publication, browser interaction, or destructive system action is permitted in this lease.
