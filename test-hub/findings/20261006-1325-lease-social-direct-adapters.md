# Lease — social direct adapters
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-06
RUN: none
JOB: social-direct-adapters
COMMIT: none
SUPERSEDES: none

## Objetivo
Implementar adaptadores independentes para instagram:primary, threads:primary e x:primary sobre o contrato multicanal PROVEN, sem mutar queue, Kwai ou TikTok.

## BASELINE_PROVEN
test-hub/findings/20261006-0850-distributor-multichannel-destination-key-proven.md — destination_key, lease_generation, publication_started e confirmation_evidence estão em produção.

## FAILED_AVOIDED
Evitar Metricool como dependência adicional; evitar reutilização de credenciais entre contas; evitar marcar publicação como concluída apenas por HTTP de publish. X oficial pago permanece fora do caminho gratuito até autorização explícita de custo.

## SUCCESS_SIGNAL
Contratos dos três adaptadores passam testes fail-closed; Instagram/Threads chegam a AUTH_REQUIRED quando credenciais Meta faltam; X possui caminho gratuito isolado e sem falso CONFIRMED.

## FAILURE_SIGNAL
Qualquer adaptador confirma publicação sem remote_id/evidência ou mistura account_id.

## TEST_VALIDITY
Testes precisam validar destination_key, auth gate, started-before-complete e confirmação específica; ausência de credencial é AUTH_REQUIRED, não FAILED.

## Expiração
2026-10-06T13:55:00Z.
