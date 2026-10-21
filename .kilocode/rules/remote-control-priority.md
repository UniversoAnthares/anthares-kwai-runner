# Controller priority — Anthares owner requirement

For every desktop operation, consult `docs/REMOTE_CONTROL_PRIORITY.md`.

Select controllers strictly in this sequence:
1. Anthares Remote
2. WinRemote
3. Remote Desktop Commander
4. MeshCentral
5. AI Commander

Only fail over after the previous controller is unavailable, insufficient for the requested capability, or fails technically. Record the cause. Never bypass security denials, execute duplicate mutations or bypass the owner's consent. Keep CORTES-only processes hidden, silent and in the background. Include this priority when delegating work.
