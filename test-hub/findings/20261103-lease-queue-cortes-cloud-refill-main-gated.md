# Lease — incorporação inativa do refill hospedado Kwai
STATUS: RUNNING
AREA: queue
DATE: 2026-11-03
RUN: https://github.com/UniversoAnthares/anthares-clipper/pull/231
JOB: none
COMMIT: 53c89840611397fe60b3853e9478c0f30def33e3
SUPERSEDES: none
LEASE_OWNER: ChatGPT / Reestruturação e Otimização / CORTES
LEASE_START_UTC: 2026-11-03T21:44:57.042Z
LEASE_EXPIRES_UTC: 2026-11-03T22:04:57.042Z
GOVERNANCE_MANIFEST: 223433740e807a90
BASE_CLIPPER_MAIN: 8c31afffe137a9ed1d9860d10e8c8d380b3a86ec

## BASELINE_PROVEN
- Titular pediu concluir migração dos workflows, preservando quotas e PC fora do executor.
- PR privada Clipper #231 é draft, contém cortes_short_dispatch.py, cortes-kwai-dispatch-refill.yml e teste; runner do workflow muda de Windows self-hosted para Ubuntu 24.04.
- Workflow tem apenas workflow_dispatch, sem schedule, condicionado a vars.CORTES_CLOUD_REFILL_ENABLED == '1'.
- Consulta Github CLI autenticada retornou 404 para variável CORTES_CLOUD_REFILL_ENABLED; gate OFF. Publicador Neon novo é PR draft #2057, default-off. Nada pode publicar por esta atualização.
- Testes de módulo Python foram preparados, ainda sem execução hosted; dado isto, a produção não deve ser ativada.

## FAILED_AVOIDED
- Não habilitar flag, workflows ou scheduler; não rodar job, publicar vídeo, mover dados, editar Neon/Cloudflare.
- Não mesclar PR pública #2057 ou ativar função, ainda sem QA. Não repetir UNCERTAIN.
- Não alterar os dois workflows daily/resume; fonte/ledger remotos pendentes.

## SUCCESS_SIGNAL
- PR privada #231 merged apenas se SHA/base/3 arquivos intactos, main com Ubuntu/sem Windows no refill e var inexistente.
- Nenhum novo job/run; callback/filas/sessões inalterados. Registro de recibo e rollback via revert PR posterior.

## FAILURE_SIGNAL
- Variável habilitada, HEAD inesperado, concorrente, arquivo extra, workflow remoto disparado, recusa ou limite de quota.

## TEST_VALIDITY
Instalação inativa do código de refill, sem homologação funcional nem corte de publicador. Nova lease específica exigida para ativar variável após reconciliação dos 68 registros e testes hosted.
