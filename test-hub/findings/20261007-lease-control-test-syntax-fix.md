# Lease — correção sintática do teste de integração de controle
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-07
RUN: none
JOB: MDE9nE00YIndrW2UFftCo3
COMMIT: pending
SUPERSEDES: none
EXPIRES: 2026-10-07T16:15:00Z

## Objetivo
Corrigir somente a estrutura Python inválida em `tests/test_control_publisher_integration_final.py`, preservando os casos e o comportamento fail-closed do teste. Nenhuma implementação de control plane, lease, fila, publicação ou deploy será alterada.

## BASELINE_PROVEN
A auditoria local detectou `elif` após blocos `try` sem estrutura sintática válida; `py_compile` falha antes de executar qualquer caso.

## FAILED_AVOIDED
Não remover casos negativos, não relaxar asserções, não alterar geração de lease, não transformar falha de harness em PASS e não executar publicação real.

## SUCCESS_SIGNAL
Todos os casos existentes compilam e os casos positivos/negativos produzem os mesmos sinais esperados, com `py_compile` e execução offline.

## FAILURE_SIGNAL
Um caso deixa de existir, uma asserção é enfraquecida, o teste continua sem compilar ou um caso negativo passa sem validar a fronteira.

## TEST_VALIDITY
Somente `py_compile` e execução local do próprio script; nenhum endpoint ou serviço externo é acessado.
