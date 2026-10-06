# CHAT2 items 2-8 — final acceptance closure
STATUS: PROVEN
AREA: kwai-publish
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37410433751
JOB: 112097393109
COMMIT: e10bc3a6dbc0b77ea047c5ccd1cb6d37ebf34cb9
SUPERSEDES: test-hub/findings/20261006-lease-chat2-items-2-8-closure.md

## Objetivo
Executar os itens 2, 3, 4, 5, 6, 7 e 8 do escopo CHAT2 sem depender da autenticação Kwai real e sem produzir publicação real desnecessária.

## Resultado
Todos os invariantes das sete frentes passaram em uma aceitação única executável.

Item 2 — UNCERTAIN/reconciliação:
- falha pós-commit entra em UNCERTAIN;
- reconciliação é observation-only;
- complete exige evidência positiva;
- nenhum caminho de reconciliação chama o publisher.

Item 3 — contrato de publicação:
- identidade de job, conta e mídia é obrigatória;
- prepare/commit são fases explícitas;
- a fronteira irreversível só aparece depois de READY.

Item 4 — seleção/identidade de mídia:
- MediaStore exige exatamente uma correspondência;
- matcher da galeria exige identidade única;
- SHA-256 participa da identidade da mídia;
- duplicidade/ambiguidade falha fechado.

Item 5 — driver de composer:
- prepare e commit são separados;
- READY_TO_PUBLISH é persistido antes do commit;
- job_id, nome, SHA e título precisam coincidir antes do commit;
- não há clique irreversível durante prepare.

Item 6 — integração com control plane:
- cliente está pinado no control v16;
- lease_generation acompanha started/complete/fail/renew;
- heartbeat usa renew com a mesma geração;
- claim exige source_id/source_start/source_end.

Item 7 — independência do PC:
- caminho produtivo auditado sem localhost, Windows, PowerShell, MEmu ou caminhos C:\Users/C:/Users;
- pc_fallback permanece desabilitado;
- executor final continua remoto.

Item 8 — canário:
- publicação real exige enable_real_publish=YES;
- o próprio workflow informa que isso só deve ocorrer após kwai-login READY;
- publicação é serializada por concurrency sem cancelamento;
- pushes executam somente o self-test da fila;
- nenhuma publicação real foi disparada por esta aceitação.

## Evidência decisiva
O job emitiu CHAT2_ITEMS_2_8_ACCEPTANCE_PROVEN e todos os 24 checks retornaram 1, incluindo:
uncertain_observation_only,
publish_failure_enters_uncertain,
complete_requires_evidence,
structured_identity_gate,
explicit_phases,
media_unique_before_selection,
sha_in_identity,
prepare_before_commit,
ready_file_binds_identity,
v16_pinned,
generation_fenced,
heartbeat_fenced,
claim_requires_canonical_interval,
production_path_has_no_pc_dependency,
pc_fallback_disabled,
manual_real_publish_gate,
serialized_publication,
push_path_never_publishes,
5 verificações de sintaxe Bash/Python.

## Consequência
A implementação autônoma do CHAT2 para os itens 2-8 está fechada. A única etapa que permanece fora deste finding é a aceitação de publicação real na conta Kwai correta, dependente do contrato READY do CHAT1. Nenhuma nova matriz deve ser aberta para estas mesmas invariantes sem evidência causal nova.
