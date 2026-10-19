# Independent SSH recovery for Anthares / CORTES

## Transport and authority

The standard GitHub-hosted Ubuntu runner joins the existing free Tailscale
network using GitHub OIDC, then talks directly to Windows OpenSSH. It never
calls the Anthares Remote MCP, HTTP job API, private issue queues, or agent.
Neon remains the existing data/control infrastructure. Render is excluded.

Tailscale authorizes only `tag:anthares-ssh-recovery` -> `100.89.147.45` TCP 22.
Windows now binds SSH only to loopback and that private IPv4. Its dedicated
firewall allow rule is scoped to TCP 22, the sshd executable, that destination,
the Tailscale interface and Tailscale source range; the tag policy enforces
client identity within that range. There is no public port forward.
The Tailscale account was verified as Free in its console.

The dedicated GitHub SSH key has a forced command and `restrict`. It cannot
open an interactive shell, forward ports/agent/X11, or run arbitrary commands.
Only `probe`, `observe`, and `recover` with a bounded opaque request ID work.
The key is not interchangeable with the original local recovery key.
Its private value belongs only in the encrypted `ARA_SSH_PRIVATE_KEY` secret
of the `anthares-ssh-recovery` GitHub environment; never in a workflow, log,
artifact, issue, report or repository. The environment allows only `main` and
the explicitly authorized validation branch.

`probe` is read-only. `recover` cannot stop/restart agents or Windows. It can
only wake the existing enabled `Anthares Remote Recovery` SYSTEM task. That
task remains the local authority and its `IgnoreNew` policy prevents competing
scheduled invocations. The disabled legacy watchdog is not enabled or changed.
The existing cold-reserve arbiter is not changed or bypassed.

## Recovery gates

- One GitHub concurrency group serializes all workflow invocations.
- A Windows global mutex serializes requests from every SSH caller.
- No existing principal, reserve, supervisor, or running recovery task may be
  present. Existing local owners always take precedence.
- At least 90 seconds of observations, with gaps no longer than 35 seconds,
  must establish absence. Stale/future evidence fails closed.
- The SYSTEM task's principal, enabled state, exact action and `IgnoreNew`
  policy must validate. Its recovery/supervisor source hashes are pinned to the
  audited live versions. A future legitimate change requires revalidation.
- The existing global execution-transition mutex is acquired and process/task
  state rechecked immediately before waking canonical recovery.
- A 120-second cooldown is written before the side effect. Crashes/retries do
  not blindly repeat it. No synthetic failure is injected into production.

The independent monitor runs on a five-minute, best-effort GitHub schedule.
It uses the existing public `/health` endpoint only as a cheap trigger hint:
a fresh device heartbeat avoids private login, not a claim of execution health.
If unavailable/stale, it rechecks after 90 seconds and dispatches the SSH
workflow; primary HTTP failure never prevents SSH dispatch. Windows then
independently verifies absence for its own 90-second grace. GitHub cannot
promise a 90-second recovery SLA. Local recovery remains faster and primary.

The Personal plan currently lists 1,000 ephemeral-resource minutes/month.
Before private login, the SSH workflow accounts all its attempts (including
reruns) in the preceding 31 days via read-only GitHub metadata. At more than
120 attempts it fails closed. Six-minute job timeouts reserve at most 720
minutes for these attempts, leaving headroom for cleanup and setup tests.
Other use of the shared tailnet quota must still be monitored. Unavailable
accounting blocks private login; it never enables billing or a paid fallback.

## Operations

Workflow: `.github/workflows/anthares-ssh-recovery.yml`.
Use manual mode `probe` to verify transport and privileged identity. The
required evidence is `SSH_INDEPENDENT_PROVEN=1` plus the validated Windows JSON,
not just a green job. The script enforces `RUNNER_ENVIRONMENT=github-hosted`.

Only after external proof, canonical-source review, and deployment to the
default branch may `ANTHARES_SSH_AUTORECOVERY_ENABLED=true` activate scheduled
recovery. A healthy machine returns a no-op. A no-op is not a repaired failure.
Actual recovery needs the distinct `SSH_CANONICAL_RECOVERY_PROVEN=1` signal.
If it never encounters a genuine failure, actual recovery remains unproven.

ChatGPT Work or another authorized caller may dispatch and inspect this
workflow using independent GitHub authentication. That integration is a
dependency; the local Codex conversation is not itself an external executor.

## Validation and rollback

PowerShell policy tests cover grace, existing owners, task validation, stale
state, future timestamps and cooldown. Local restricted-key login validated
the administrator token and live task pins while leaving agents intact.
The first hosted run failed closed at missing-secret preflight. Later the
real independent SSH probe passed in run 39249878095, attempt 3, source
ab47afb6656d034031bcf0abde16c0e0546bc1b7. It emitted
`SSH_INDEPENDENT_PROVEN=1`, hostname DESKTOP-FTDK0HP, administrator=true,
primary_count=1, reserve_count=0 and action_performed=false. This proves the
independent channel, not a repaired real failure. Neither agent nor publisher
was stopped to obtain evidence.

Disable the repository activation variable to stop scheduled repair attempts.
Revoke the dedicated public key line ending in
`anthares-github-ssh-recovery-20261019` to revoke this channel, preserving all
other keys. Remove only its specific firewall allow rule if necessary. Keep
the original loopback configuration backup and do not alter CORTES publishers.

References:
- https://docs.github.com/en/actions/reference/runners/github-hosted-runners
- https://tailscale.com/docs/integrations/github/github-action
- https://tailscale.com/docs/features/workload-identity-federation
- https://tailscale.com/pricing
