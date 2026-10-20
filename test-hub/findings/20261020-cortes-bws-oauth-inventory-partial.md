# CORTES OAuth Google: Bitwarden inventory inaccessible with current SDK
STATUS: PARTIAL
AREA: architecture
DATE: 2026-10-20
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39511953159
JOB: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/39511953159/job/118934894855
COMMIT: f590aa8e88bd502e285bd67db0f2552b94ed3112
SUPERSEDES: 20261020-cortes-bws-google-oauth-inventory-running.md

## Objetivo
Verificar sem revelar valores se Anthares Secrets Automation já contém cliente OAuth Google reutilizável.

## Resultado
Tentativa de metadados pelo SDK oficial pinado @bitwarden/sdk-napi@1.0.0 executou em GitHub-hosted, pacote instalado com êxito, mas autenticador retornou `CORTES_BWS_INVENTORY_ERROR_KIND=Error` sem `CORTES_BWS_AUTH=PASS`. Não houve listagem de segredos nem credenciais Google verificadas. SDK/arquivos temporários removidos pelo job. **O erro não demonstra que o projeto/segredo esteja ausente**. O teste de leitura Bitwarden sm-action com UUID conhecido permanece a evidência anterior comprovada, não uma permissão de inventário.

## Correção
O workflow e script de auditoria inválidos são removidos em PR subsequente. Não repetir login SDK com o mesmo bootstrap, pois este percurso falhou na autenticação. Consultas ao cofre deverão usar integração validada e IDs explicitamente autorizados, ou credencial de conta de máquina corretamente provisionada para o Anthares Automation.

## Estado CORTES
rclone no Windows instalado e pasta Perfil 9 testada. Perfil 3 autorizado, mas upload falhou HTTP 403 rateLimitExceeded do client_id rclone compartilhado; Perfil 2 sem autorização. PR #101 em anthares-clipper isolou backup após despacho e bloqueou cliente compartilhado até OAuth próprio. Não mover tokens localmente para BWS sem credenciais e teste real de escrita/leitura. Preservar masters e publicações.
