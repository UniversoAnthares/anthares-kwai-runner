# SpawnDroid Hub — contrato de evidência e teardown (AGENTE 02)
STATUS: RUNNING
AREA: android
DATE: 2026-11-14
RUN: none
JOB: GitHub-hosted PR contracts (pending)
COMMIT: 5db0bf2ef1e0ed0f1cb930a563090415d686cd0e
SUPERSEDES: none

## Objetivo
Endurecer o canário cloud sem ativar Kwai em produção, com evidência WebDriver real e confirmação terminal por API do provedor, evitando falsas confirmações.

## Causal chain / Test Hub
BASELINE_PROVEN: GitHub run 43552154737 tem contracts SUCCESS e remote-canary SKIPPED; PRs 2605–2607 merged.
FAILED_AVOIDED: Não repetir canário real sem APK validado pelo AGENTE 01, plano e saldo consultados, chave com escopo e exclusividade de sessão. Não repetir POST ambíguo.
SUCCESS_SIGNAL: offline CI PASS; futuro canário real com ID Android, dispositivo ARM64, Kwai foreground, UI source, encerramento terminal via API e consumo verificado.
FAILURE_SIGNAL: comando WebDriver falho, estado do app != foreground, package incorreto, API terminal ausente ou quota 402/429.
TEST_VALIDITY: contratos offline são simulações; teste real somente com os preflight gates verificados. Resultado skipped não valida Android.

## Escopo e lease de edição
OWNER: AGENT-02 / branch agent02/spawndroid-hub-safety-20261114
FILES: tools/kwai_spawndroid_stable_hub.py; tests/test_kwai_spawndroid_stable_hub.py; .github/workflows/kwai-spawndroid-hub.yml; .github/workflows/kwai-spawndroid-preflight.yml.
MUTEX: proposta de PR isolada; não tocar publicação, contas, Neon ou ci-hub/executor-routing.json.
