# Lease — deploy CORTES WordPress
STATUS: RUNNING
AREA: wordpress-deploy
DATE: 2026-10-14
RUN: none
JOB: deploy-cortes-live
COMMIT: none
SUPERSEDES: none
OWNER: chatgpt-cortes-finalization
LEASE_START_UTC: 2026-10-14T00:14:00Z
LEASE_EXPIRES_UTC: 2026-10-14T00:44:00Z

## Objetivo
Concluir a pendência de publicação e validação da versão atual do plugin `anthares-clipper` no WordPress real de anthares.us, sem WPVibe e sem depender do PC como executor do pipeline de vídeo.

## BASELINE_PROVEN
O repositório `UniversoAnthares/anthares-wordpress` possui o plugin `anthares-clipper`; o GitLab espelho possui credenciais SSH de QA já usadas para alcançar o servidor WordPress.

## FAILED_AVOIDED
Não usar Browserless, que nesta rodada está sem unidades. Não depender de Anthares Remote/WinRemote, que estão offline. Não repetir GitHub Actions privado sem runner, pois o CI CORTES falhou antes de iniciar etapas.

## SUCCESS_SIGNAL
Job remoto via GitLab conecta ao Hostinger, atualiza `~/anthares-wordpress-bootstrap` para `origin/main`, aplica somente `anthares-clipper/` em `wp-content/plugins/`, executa PHP lint, confirma versão/sha e consulta o estado CORTES pelo WP-CLI no ambiente real.

## FAILURE_SIGNAL
Falha de autenticação SSH, divergência inesperada do repositório no servidor, erro de lint, rsync incompleto ou ausência das funções/rotas CORTES no WordPress real.

## TEST_VALIDITY
A validação só conta se o job alcançar o host real e emitir evidência pós-deploy do arquivo vivo e do WP-CLI. Falha de runner/CI antes do SSH é INVALID, não falha do plugin.
