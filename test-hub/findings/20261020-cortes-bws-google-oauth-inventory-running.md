# Auditoria read-only Anthares Secrets: CORTES Google OAuth
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-20
RUN: pending
JOB: pending
COMMIT: pending
SUPERSEDES: none

## BASELINE_PROVEN
O workflow Anthares Secrets Remote Smoke usa `secrets.BWS_ACCESS_TOKEN` para ler segredo de teste via bitwarden/sm-action sem imprimir o valor. Google Drive via rclone possui remotes para Perfil 3 e 9, mas o cliente OAuth compartilhado foi limitado por erro 403 rateLimitExceeded. O runner SYSTEM não possui credencial de máquina BWS Automation detectada.

## FAILED_AVOIDED
Não repetir upload desassistido com cliente OAuth compartilhado. Não buscar valores de segredos Bitwarden em logs, não usar browser/Chrome em janela ativa. Não fazer mutações Bitwarden. Não inferir alcance do projeto Anthares Automation a partir do segredo de teste Anthares AI.

## SUCCESS_SIGNAL
Um workflow GitHub-hosted retorna BWS_AUTH=PASS e informa somente existência/contagem de nomes de segredos potencialmente relacionados a Google OAuth, sem valores, juntamente com alcance do projeto Anthares Automation.

## FAILURE_SIGNAL
BWS_AUTH=FAIL, BWS_SCOPE_UNKNOWN ou token de máquina sem permissão de listagem; sem tentativa de escalar permissões.

## TEST_VALIDITY
GitHub Actions executado com `secrets.BWS_ACCESS_TOKEN` no repositório que já possui a integração comprovada. Teste é apenas leitura, sem tocar publicações ou arquivos de usuário. Uma conclusão verde sem as marcas de sucesso é parcial.
