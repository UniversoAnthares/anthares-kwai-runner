# Canonical Anthares Remote runtime

The canonical Windows administration channel is the Anthares Remote Agent running as SYSTEM in session 0.

Primary control transport: private GitHub/GitLab issue queues.

Recovery root: `C:\ProgramData\AntharesRemoteAgent\recovery-watchdog.ps1`.

The watchdog repairs/restarts the canonical SYSTEM scheduled task and any installed MeshCentral/WinRemote Windows services. HTTP controllers remain auxiliary and are not required by the canonical runtime.
