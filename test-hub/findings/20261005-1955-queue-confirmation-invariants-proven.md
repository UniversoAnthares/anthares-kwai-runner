# Confirmação positiva da fila agora é fail-closed no snapshot
STATUS: PROVEN
AREA: cloudflare
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37388863529
JOB: 112028875882
COMMIT: 83e45c43c001766c8fc179e28d278c44a64d3b68
SUPERSEDES: test-hub/findings/20261005-1935-qa-central-confirmation-invariant-gap.md

BASELINE_PROVEN: lifecycle central e dedupe já existentes.
FAILED_AVOIDED: complete não confia mais em confirmed=true antes de started; reconcile não confirma fora de uncertain; confirmação positiva sem remote_id ou confirmation_evidence é rejeitada.
SUCCESS_SIGNAL: runner público valida as guardas e self-test contém rejeições explícitas de confirmação prematura/sem evidência.
FAILURE_SIGNAL: ausência de qualquer guarda ou aceitação de caminho prematuro.
TEST_VALIDITY: prova de snapshot; não equivale a deploy no Worker.

## Objetivo
Fechar a lacuna de segurança apontada pelo QA no próprio controlador.

## Resultado
PROVEN no snapshot. complete confirmado exige owner correto, status leased, publication_started=1 e remote_id/confirmation_evidence. reconcile exige status uncertain e evidência positiva para confirmed=true. Self-test inclui rejeição antes de started, rejeição de reconcile sem evidência e rejeição de complete sem evidência.

## Evidência decisiva
Run 37388863529 / job 112028875882: Validate central safety invariants = success.

## Consequência
Chamadores que não possuem remote_id devem fornecer confirmation_evidence explícita. Não afrouxar esta guarda para compatibilidade; adaptar o chamador. Produção ainda depende de deploy real do Worker.
