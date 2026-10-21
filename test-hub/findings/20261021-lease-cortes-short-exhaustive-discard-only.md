# Lease: produção exaustiva de curtos CORTES
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-21
RUN: none
JOB: none
COMMIT: 74e1f6b534313ff1fe7bca526a6cba496f1c205c
SUPERSEDES: none
LEASE_AREA: cortes-short-selection-and-production
LEASE_OWNER: ChatGPT current conversation
LEASE_MAX_EXPIRY_UTC: 2026-10-21T12:43:24.333Z

## Objetivo
IA avalia transcrição exclusivamente para excluir trechos inúteis; planejador determinístico transforma todo conteúdo restante em cortes curtos sem nota editorial nem mínimo/máximo artificial de quantidade. Mantém duração de 30-90s após microedição e layout vertical.

## BASELINE_PROVEN
Clipper GitHub main bc80cba33be312ba1e15af84ad23402968762274; GitLab main 64f51fab9866cb9123acbc0931ed3ea257f4fc5b (divergente). Lease 20261021-0740-lease-cortes-five-short-networks.md cobre redes, área independente.

## FAILED_AVOIDED
Preservar materiais publicados/armazenados e lock de fonte; não espelhar GitLab divergente; nenhuma publicação sem validação.

## SUCCESS_SIGNAL
Testes com cobertura exaustiva, sem nota mínima, sem teto de 100, planos imutáveis, e microedições/layout/duração mantidos.

## FAILURE_SIGNAL
Candidato rejeitado por nota, quota artificial, perda de ledger ou saída fora dos limites.

## TEST_VALIDITY
Unittest sintético prova lógica; CI e execução real ainda exigem evidências independentes.
