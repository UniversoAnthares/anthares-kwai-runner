# AI Commander helper repair + MeshCentral recovery
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-07
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

## Objetivo
Restore AI Commander privileged execution and repair the MeshCentral recovery path on aic-lucas-pc.

## Resultado
MeshCentral recovery server was restarted successfully. Port 4432 is listening on loopback, Mesh Agent is Running/Automatic, and an established agent connection to 4432 was observed. The MeshCentral MCP start-local.ps1 wrapper was corrected from the obsolete 4430 endpoint to 127.0.0.1:4432, switched to the user-writable Node runtime, and now loads the existing local MeshCentral admin credential at runtime without storing it in Git.

AI Commander 1.4.1 remains online for normal remote execution. Its installation is intact (integrity.ok files=80), but elevated execution reports not_registered because the SYSTEM task "AI Commander Privileged Helper" is absent. The signed helper files are present. The official 1.4.1 Windows installer was downloaded to the authorized PC and its Authenticode signature verified as Valid with publisher WEARFITS sp. z o.o. Starting the installer is the remaining admin/UAC step; remote launch was blocked by the execution safety layer.

## Evidência decisiva
MeshCentral after restart: task=Running; PORT4432=True; Mesh Agent=Running; AGENT_CONN4432=True; wrapper4432=True; wrapper credential loader=True.
AI Commander status: ONLINE, elevatedUnavailableReason=not_registered. Official installer signature: Valid.

## Consequência
Preserve the proven MeshCentral 4432 instance. Do not revert the MCP wrapper to 4430. Do not recreate MeshCentral credentials. For AI Commander, run the already verified official installer with Windows administrator approval, then verify that the "AI Commander Privileged Helper" SYSTEM task exists and elevatedExec becomes available.