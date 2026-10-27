# Threads 869–909 — verificação editorial externa
STATUS: RUNNING
AREA: github
DATE: 2026-10-27
RUN: pending PR
JOB: pending
COMMIT: pending
SUPERSEDES: none

## BASELINE_PROVEN
Fila Neon: clip queued/isolated, sha256 91c12a91fb5a6d6cf87846120c99588029f85307a39ac9e782db11918d3af481. Job externo anterior #40559374218 comprovou checksum e ASR para 829–869.

## FAILED_AVOIDED
Não gravar trabalho no PC, não publicar no Threads nem desbloquear sem evidência; não deixar job recorrente.

## SUCCESS_SIGNAL
ASR_VERIFIED, WP attachment único e SHA-256 exato nos logs, transcrição comprovada no artifact.

## FAILURE_SIGNAL
Download, SHA, instalação ou execução falha/quota; manter isolated.

## TEST_VALIDITY
Validar logs e conteúdo de cues; o status green sozinho não comprova.
