# Controller priority — Anthares owner requirement

For every desktop operation, consult `docs/REMOTE_CONTROL_PRIORITY.md`.

Select controllers strictly in this sequence:
1. Anthares Remote
2. WinRemote
3. Remote Desktop Commander
4. MeshCentral
5. AI Commander

Only fail over after the previous controller is unavailable, insufficient for the requested capability, or fails technically. Record the cause. Never bypass security denials, execute duplicate mutations or bypass the owner's consent. Keep CORTES-only processes hidden, silent and in the background. Include this priority when delegating work.


## Mandatory owner rule — close agent-owned windows immediately (2026-10-21)
Every Copilot agent must register ownership of each temporary window, Chrome tab, PowerShell/CMD console or dialog it opens, close it immediately after use in `finally`, and ensure crash recovery cleans its verified orphans. Keep automated browser profiles isolated, invisible and muted. Never close user windows, other agents' resources or active shared services. Apply to all delegated jobs; see [AGENTS.md](../AGENTS.md) and https://github.com/UniversoAnthares/home/blob/main/AGENTS.md.
