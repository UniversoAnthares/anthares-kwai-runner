# CORTES — homologação hospedada somente-leitura recuperada
STATUS: PROVEN
AREA: architecture
DATE: 2026-11-03
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41116819377
JOB: 124273089258
COMMIT: 10bc8c6009fec8415a3ebc71e6bd6a7ff90e922f
SUPERSEDES: 20261030-cortes-hosted-ffmpeg-runtime-running.md
RECONCILED_AT_UTC: 2026-11-03T20:15:31.465Z

## Objetivo
Encerrar a cadeia de teste hospedado de 2026-10-30 que permaneceu marcada como RUNNING após a execução final.

## Resultado
A última execução da cadeia foi completed/success em 2026-10-30, run 41116819377. O job readonly-proof concluiu com sucesso. Nos logs de execução, separados do texto dos comandos, constam:
- CORTES_HOSTED_CANONICAL_SOURCE=PASS
- CORTES_HOSTED_SOURCE_SHA=9ee0b7c2501c4bf223bbed4203c8a06f3fe9ca46
- CORTES_HOSTED_READONLY_GATE=PASS

O runner GitHub-hosted Ubuntu comprovou checkout do Clipper privado canônico, FFmpeg e dependências suficientes para preflight/compilação, sem mídia real.

## Critério e limites
PROVEN exclusivamente o preflight de código e dependências em executor hospedado efêmero. Publicação, credenciais de distribuição, mídia persistente, ledger externo, failover, quota contínua e handoff com fencing permanecem UNVERIFIED. Esta evidência não autoriza trocar o primário de CORTES, repetir publicações ou descartar cópias.

## Consequência
Usar o run 41116819377 como baseline já comprovado. Os findings 20261030-cortes-clipper-hosted-readiness-running.md e 20261030-cortes-hosted-canonical-source-running.md foram supersedidos pela cadeia indicada. O workflow hospedado de preflight está disabled_manually após a redução de Actions; manter suspenso até gate de quotas/autorização.
