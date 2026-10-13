# ARA GitHub/GitLab control-plane migration

STATUS: PARTIAL — ONE LOCAL START ACTION REQUIRED
AREA: ara-admin-control-transport
OWNER: chatgpt-ara-github-actions-migration
LEASE_START_UTC: 2026-10-13T15:53:00Z
UPDATED_UTC: 2026-10-13T16:24:00Z

PROVEN:
- The obsolete ChatGPT plugin `Anthares Remote` that pointed at Render was uninstalled.
- `UniversoAnthares/anthares-ara-queue` exists, is private, and accepts the `ara-queued` label.
- Go tests and Windows amd64 build for the queue-aware agent passed in GitHub Actions run `38425643217`.
- The Windows installation already contains `anthares-remote-agent-v4.exe`, `load-issue-queue-auth.ps1`, and the DPAPI credential file `secrets/issue-queue.json`.
- The canonical supervisor was changed so GitHub/GitLab issue queues are primary transports; `onrender.com` and `workers.dev` are explicitly excluded from automatic HTTP candidates.
- Automatic Cloudflare-only finalizers/deploy triggers were removed or made manual-only after the user reported Cloudflare quota exhaustion.
- A safe queue smoke issue exists as `UniversoAnthares/anthares-ara-queue#2` and remains `ara-queued` awaiting the local queue-aware agent.

SUPERSEDED:
- The self-hosted GitHub Actions runner diagnostic remained queued/offline and was removed. The user's Windows PC is not used as a GitHub Actions runner.
- Cloudflare-only finalization is not an accepted recovery architecture while quota is exhausted.
- Render is not an accepted control transport.

CURRENT_BLOCKER:
- During the one-time migration, the command stopped the running `Anthares Remote Agent SYSTEM` scheduled task and its legacy agent before the final `Start-ScheduledTask` line could execute; the control connection therefore terminated as designed before it could restart itself.
- WinRemote and MeshCentral recovery channels were also unavailable at that moment.
- Because all remote administration transports are now offline, the remaining action cannot be performed remotely in this session.

NEXT_SINGLE_ACTION:
- On Windows Task Scheduler, run the existing task `Anthares Remote Agent SYSTEM` once. The task points to `C:\ProgramData\AntharesRemoteAgent\run-agent-system-supervisor.ps1`, which has already been replaced with the queue-first V5 supervisor. No reinstall, command prompt, or credential entry is required.

SUCCESS_SIGNAL_AFTER_START:
- `system-supervisor-state.json` reports `mode=issue-queues-only` (or `issue-queues+optional-http` only if a non-Render/non-Cloudflare optional control is explicitly configured), `github_queue=true`, `cloudflare_required=false`, `render_required=false`.
- Private queue issue #2 is consumed and acknowledged/closed by the agent.
