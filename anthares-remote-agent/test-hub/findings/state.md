# Anthares Remote — validation state

Updated: 2026-10-13

## PROVEN

- Cloudflare control is operational on `DESKTOP-FTDK0HP`.
- Real remote execution completed successfully. Final evidence job: `b5960b6659924a3885e2d09c679d9679`, output `ARA_FINAL_VALIDATION_OK`, exit code 0.
- A second real Windows probe completed successfully. Job: `38bd515006db45c5b4c82bbae4650059`, Windows `10.0.19045.6093`, exit code 0.
- Real system information retrieval succeeded during this recovery.
- Mutable work root is `D:\AntharsWork`; `TEMP`, `TMP` and `ANTHARES_WORK_ROOT` are directed there and `ANTHARES_ALLOWED_ROOTS` includes it.
- Canonical SYSTEM supervisor writes logs/state under `D:\AntharsWork` and filters legacy `onrender.com` controls. `render_required=false` is recorded by the supervisor design.
- Canonical SYSTEM supervisor commit: `77cd13c17896e897839520b55428836f68ec895c`.
- Clean hidden user-fallback watchdog commit: `1d52c63e31e171158bf5e429595d954856ce6042`.
- Private GitHub queue `UniversoAnthares/anthares-ara-queue` is accessible with the existing machine credential; queue redundancy is preserved through its separate hidden scheduled bridge.
- Existing user-layer scheduled tasks were hardened with Hidden, StartWhenAvailable, zero execution time limit, restart count 99, one-minute restart interval, and IgnoreNew multiple-instance policy.
- Duplicate `anthares-remote-agent-v4.exe` and its stale watchdog were removed after PID/parent verification. Final runtime audit showed one `anthares-remote-agent.exe` process.
- The existing C: job spool was copied/staged to `D:\AntharsWork\ara-jobs` before any attempted path migration. The source remained intact after the privileged rename was denied.
- Local closure evidence is stored at `D:\AntharsWork\legacy-pc-runtime\state\closure-20261013.json`.
- BlueStacks audit is stored at `D:\AntharsWork\legacy-pc-runtime\state\bluestacks-audit.json`.

## ADMIN FINALIZATION PREPARED

`D:\AntharsWork\admin-finalize.ps1` is an idempotent privileged finalizer. It performs these operations only after confirming Administrator context:

1. preserves/stages job spool contents on D: and replaces `C:\ProgramData\AntharesRemoteAgent\jobs` with a junction to `D:\AntharsWork\ara-jobs`;
2. registers `Anthares Remote Agent SYSTEM` as SYSTEM / Highest / Hidden / AtStartup with zero execution time limit and restart policy;
3. launches `C:\ProgramData\AntharesRemoteAgent\run-agent-system-supervisor.ps1` in hidden non-interactive mode;
4. performs the handoff from user-session agent processes to session 0;
5. writes privileged validation evidence to `D:\AntharsWork\legacy-pc-runtime\state\admin-finalize.json`.

Finalizer SHA-256 at preparation time: `B0C340E84B1342FB9FFA50D85398D25EC4E945FD951CAD9D48A6716CD3D94590`.

## PENDING PRIVILEGED VALIDATION

These items require a working elevated administrative channel on the Windows host:

- `Anthares Remote Agent SYSTEM` task registration and proof;
- agent process in Windows session 0;
- C: jobs-path junction to `D:\AntharsWork\ara-jobs`.

Current administrative bridges were unavailable during the recovery: WinRemote reported `tunnel_client_not_seen`; MeshCentral reported a terminated session. The Cloudflare agent executes as the non-elevated user and receives Access Denied for SYSTEM task registration and protected ProgramData directory rename.

## CURRENT RUNTIME STATE

- Active proven agent: `anthares-remote-agent.exe`.
- Active agent session: 3 pending privileged handoff.
- SYSTEM task: absent pending privileged finalization.
- User fallback task: hidden and ready, with the clean fallback script already deployed for its next trigger.
- GitHub queue bridge: present and hidden.
- Canonical active control: Cloudflare Workers.
- Render required by canonical runtime: false.
- Job spool redirection to D: pending privileged finalization; complete source data was staged on D: first.
- C: free space during final audit: approximately 2.128 GiB.

## BLUESTACKS

BlueStacks is absent from the D: installer area and is not installed. Installation remains gated by available system-drive space and administrator privileges. No installation was attempted in this recovery state.

## STATUS RULE

Only practical Windows/Cloudflare evidence is marked PROVEN. Items awaiting the privileged finalizer remain pending until `admin-finalize.json`, session-0 process evidence, the SYSTEM scheduled task, and the jobs junction are observed on the host.
