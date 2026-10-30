# CORTES hosted — FFmpeg ausente após autenticação canônica comprovada
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-30
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41116638877
JOB: 124272455874
COMMIT: pending
SUPERSEDES: 20261030-cortes-hosted-canonical-source-running.md

## BASELINE_PROVEN
- Runner Github-hosted Ubuntu executou checkout e clonagem privada do GitHub canônico.
- Prova em log: CORTES_HOSTED_CANONICAL_SOURCE=PASS; CORTES_HOSTED_SOURCE_SHA=9ee0b7c2501c4bf223bbed4203c8a06f3fe9ca46.
- O preflight passou a checagem de arquivos do Clipper, mas falhou em CORTES_HOSTED_FFMPEG_UNAVAILABLE no run 41116638877.
- Produtores Windows e ledgers persistentes permanecem inalterados.

## FAILED_AVOIDED
- Repetir o checkout do GitLab desatualizado.
- Migrar produção antes da prova de FFmpeg, pacotes, checkpoint e identidade de publicação.
- Executar comandos ou processar mídia no Windows para testar cloud.

## SUCCESS_SIGNAL
O novo job público em Ubuntu instala FFmpeg/ffprobe somente no runner efêmero, finaliza compilação e preflight, e publica o marcador CORTES_HOSTED_READONLY_GATE=PASS.

## FAILURE_SIGNAL
Erros APT, CORTES_HOSTED_PYTHON_DEPENDENCIES_FAILED, CORTES_HOSTED_COMPILE_FAILED, CORTES_HOSTED_MEDIA_PREFLIGHT_FAILED ou outros com causa concreta.

## TEST_VALIDITY
Somente leitura e compilação, sem vídeos nem publicações, sem manipulação de filas e credenciais expostas. Esta etapa ainda não prova ledger compartilhado, autenticação de publicação ou cutover.
