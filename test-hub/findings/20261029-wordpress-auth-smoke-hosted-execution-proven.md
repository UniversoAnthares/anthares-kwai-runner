# WordPress smoke: hosted runner proven; original AUTH_MISSING preserved
STATUS: PROVEN
AREA: wordpress-auth-smoke/cloud-offload
DATE: 2026-10-29
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40919557891
JOB: 123608780179
COMMIT: 2057fb50e1138ae34319778603d2874cb42f17c7
SUPERSEDES: lease-20261029-wordpress-smoke-hosted.md

## Evidência externa
Execução real em GitHub Actions 1000049365, ubuntu-24.04. Checkout e setup-python passaram; script tools/cortes_wp_auth_smoke.py executou fora do PC e emitiu CORTES_WP_AUTH_SMOKE=AUTH_MISSING, exit code 2, mantendo o status FAILURE do CI. Baseline Windows anterior: run 40500306462, runner Anthares-QA-P0-Windows-Independent, mesmo marcador CORTES_WP_AUTH_SMOKE=AUTH_MISSING. Nenhuma chamada de escrita ao WordPress.

## Escopo
A migração de infraestrutura deste smoke test é PROVEN. A autenticação WordPress por secrets permanece PENDING; diagnóstico continua falhando explicitamente. O runner local permanece disponível para outros workflows QA-P0 até cada rota ser deslocada. O job foi migrado para o GitHub público sem exportação, alteração ou cópia de credenciais. Não repetir a mesma falha de autenticação até alteração causal.

## Observações
Peer GitLab no ref main contém a versão Windows preexistente, sem espelhamento automático. PR #1912 restrita ao workflow, à coordenação e à evidência Test Hub.
