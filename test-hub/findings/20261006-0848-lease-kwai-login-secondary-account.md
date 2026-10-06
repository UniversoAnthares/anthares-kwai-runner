# Lease — Kwai secondary account namespace
STATUS: RUNNING
AREA: kwai-login
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: none

## Objetivo
Generalizar sessão/autologin Kwai para account_id isolado e preparar kwai:secondary sem alterar estado de kwai:primary.

## Lease
OWNER: chatgpt-social-destinations
EXPIRES: 2026-10-06T13:18:00Z
SCOPE: account namespace em scripts/workflow Kwai; nenhum login real primário.

## BASELINE_PROVEN
FSM/autologin e safety de publicação existentes; kwai:primary permanece preservado.

## FAILED_AVOIDED
Sem bare ikwai://login, Activities não exportadas, coordenadas fixas ou reutilização de sessão entre contas.

## SUCCESS_SIGNAL
Scripts selecionam credenciais e arquivo de sessão por account_id; primary continua compatível; secondary falha fechado quando secrets próprios ausentes.

## FAILURE_SIGNAL
Qualquer caminho lê credenciais/sessão de primary para secondary ou altera sessão primary.

## TEST_VALIDITY
HEAD relido após lease; teste secundário só é válido com secrets KWAI_SECONDARY_* próprios.
