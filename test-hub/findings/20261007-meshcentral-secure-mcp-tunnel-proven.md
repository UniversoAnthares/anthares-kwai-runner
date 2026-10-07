# MeshCentral Secure MCP Tunnel ready
STATUS: PROVEN
AREA: architecture
DATE: 2026-10-07
SUPERSEDES: 20261007-ai-commander-helper-meshcentral-recovery.md

## Resultado
The second OpenAI Secure MCP Tunnel for MeshCentral was configured on aic-lucas-pc using the existing proven MeshCentral MCP stdio server. Profile meshcentral points to the new tunnel and invokes the local start-local.ps1 wrapper. A Windows scheduled task named Anthares MeshCentral Secure MCP Tunnel now supervises the outbound tunnel.

## Evidência
tunnel-client doctor: RESULT ok.
MeshCentral MCP stderr: Connected to MeshCentral.
Local tunnel health 127.0.0.1:8082: /healthz=live, /readyz=ready.
Scheduled task state: Running.
MeshCentral remains loopback-only on 4432; no public administrative listener was added.

## Próximo passo
Create/connect the custom ChatGPT plugin using the existing MeshCentral tunnel. No server, credential, agent, or tunnel recreation is required.