# Anthares — mandatory order of remote desktop/control providers (owner rule, 2026-10-21)

Applies to every Anthares agent, Claude/Claude Code, Codex, Kilo, Cline, Copilot and delegated agent that has access to any of these controllers, locally or in the cloud.

When controlling or administering the owner's Windows PC, use this **strict, exclusive order**:

1. **Anthares Remote** — primary, always preferred.
2. **WinRemote** — first fallback.
3. **Remote Desktop Commander** — second fallback.
4. **MeshCentral** — third fallback.
5. **AI Commander** — fourth fallback.

Selection protocol: Use the first connected, appropriately authorized controller with the capability required for that specific action. Proceed to the next ranked controller only after the preceding controller is technically unavailable, fails, or lacks that capability. Preserve the reason for failover in the operational record; skip unnecessary repeated health probes. Never use a fallback to circumvent security restrictions, access denials, missing consent, or explicit user constraints. Never execute the same mutation/publication through multiple controllers concurrently. At the next independent operation, prioritize the top-ranked provider again.

This is a permanent OWNER-MANDATED project rule. Agents must consult it at startup and carry it into delegated tasks and new execution contexts. Older instructions declaring WinRemote, Remote Desktop Commander, MeshCentral, or AI Commander generally forbidden or retired are superseded **only with respect to the ordered, authorized fallback capability**; all security and consent requirements remain in force. Do not revise or invert this priority without explicit owner approval.

Additional CORTES rule: processes dedicated exclusively to automated video cutting and publishing must run hidden, silent, in the background. Do not alter publishing schedules or queues just to validate this policy.

A repository instruction file is authoritative for agents that read it. Agents operating outside this repository must have the same rule explicitly included in their own loaded instructions; do not claim unconfigured external systems are covered.
