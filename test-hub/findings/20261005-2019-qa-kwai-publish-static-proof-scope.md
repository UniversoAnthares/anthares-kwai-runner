# QA: prova estática Kwai ainda não cobre started, identidade da conta e mídia selecionada
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37387709252
JOB: 112025101402
COMMIT: f685d58567c2f2fe328e5d60b9c2596b50ef845b
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-1927-qa-kwai-publish-safety-static-proven.md
FAILED_AVOIDED: não rebaixar os invariantes já comprovados; apenas delimitar o escopo exato da prova.
SUCCESS_SIGNAL: auditoria do workflow identifica exatamente quais invariantes o job verde realmente testa.
FAILURE_SIGNAL: encontrar assertions comportamentais para started/identidade/correlação de mídia que invalidem esta delimitação.
TEST_VALIDITY: leitura do HEAD e do workflow do run; nenhum código/publicação/sessão foi alterado.

## Objetivo
Evitar que `KWAI_PUBLISH_SAFETY_STATIC_OK` seja interpretado como prova mais ampla do que o teste executou.

## Resultado
O workflow valida sintaxe, SHA da mídia, namespace dedicado MediaStore, marcador MEDIASTORE_MATCHES=1, presença de PUBLISH_REQUESTED/UNCERTAIN/CONFIRMED e ausência de um padrão específico de sucesso por retorno à Home. Ele não testa chamada central `/started`, identidade da conta autenticada, vínculo entre MediaStore _id/content URI e o thumbnail clicado, nem reconciliação de UNCERTAIN.

## Evidência decisiva
`.github/workflows/kwai-publish-safety-validation.yml` contém somente grep/compile para esses invariantes e nenhuma assertion sobre `github-queue/started`, account identity, `_id`/content URI selecionado ou `/job/reconcile`.

## Consequência
Preservar o finding 1927 como PROVEN para seu escopo estático. Antes de PRODUCTION PROVEN, CHAT 2 deve adicionar/validar separadamente: started fail-closed antes do clique irreversível; identidade positiva da conta; correlação determinística da mídia selecionada; reconciliação segura de UNCERTAIN.