# CORTES — lease encerrada, proposta de suspensão CRON em revisão
STATUS: PARTIAL
AREA: queue
DATE: 2026-11-03
RUN: https://github.com/UniversoAnthares/anthares-clipper/pull/230
JOB: none
COMMIT: 39e2eee3366e713a3488b4f5086fff3eed3761f5
SUPERSEDES: 20261103-lease-queue-cortes-clipper-cron-pcoff.md
LEASE_CLOSED_UTC: 2026-11-03T20:15:31.465Z

## Objetivo
Encerrar a revisão sob lease da dependência de cron agendado em runner Windows pessoal, preservando os invariantes de CORTES e custo adicional zero.

## Resultado comprovado
- Draft PR #230 em anthares-clipper contém exatamente dois arquivos: .github/workflows/cortes-daily.yml e .github/workflows/cortes-kwai-dispatch-refill.yml.
- Comparação integral entre main e branch comprovou somente remoção de on.schedule (quatro linhas/139 bytes totais); workflow_dispatch, filtros push, publicação e demais passos permanecem idênticos.
- Base main clipper 9ee0b7c2501c4bf223bbed4203c8a06f3fe9ca46; branch HEAD 39e2eee3366e713a3488b4f5086fff3eed3761f5.
- GitLab espelho do Clipper carece dos dois arquivos: nenhuma sincronização foi acionada.
- Nenhum merge, upload de mídia, alteração de filas/ledgers, produção ou agendamento operacional foi executado por esta revisão.
- Único runner self-hosted encontrado: DESKTOP-FTDK0HP offline; três workflows de CORTES dependentes dele, com últimos runs de 2026-10-30.

## Limites e aceite
Esta lease de revisão está ENCERRADA. A PR #230 continua draft e aguarda homologação do proprietário operacional e plano de continuidade fora do PC. O merge depende de checkpoint/ledger persistente, fencing, quota, recuperação e continuidade do publicador. Não declarar PC retirado ou migração concluída.

## Próxima ação
Homologar cutover de CORTES externo em fluxo separado. Com autorização, mesclar a PR verificando SHA/efeitos e registrar rollback. Preservar a lista fixa dos 21 itens AOI.
