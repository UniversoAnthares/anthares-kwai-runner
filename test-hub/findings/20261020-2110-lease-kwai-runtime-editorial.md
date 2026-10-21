# Lease: normalização editorial no executor Kwai ativo
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-20
RUN: none
JOB: none
COMMIT: 0d3aca85e0246a290f8847108dbca2f65cd12de0
SUPERSEDES: none
LEASE_AREA: kwai-publish-editorial-runtime
LEASE_OWNER: chatgpt-current-conversation
LEASE_MAX_EXPIRY_UTC: 2026-10-21T01:40:00Z

## BASELINE_PROVEN
Executor Kwai físico está rodando em D:\\AntharsWork\\quota-write-20261017, HEAD local 1b38db5 com mudanças locais relevantes em worker, daemon e adaptadores. Não sobrescrever, limpar nem reiniciar. Processo do daemon está ativo. Worker é subprocesso por job, normaliza hoje o campo KWAI_VIDEO_TITLE sem sufixo obrigatório em physical_env e prepare_memu.

## FAILED_AVOIDED
Não fazer git pull sobre workspace dirty, nem reiniciar publicações, nem repetir envios incertos. Não substituir caracteres UTF8 por ASCII quando o método ADBKeyboard aceita Unicode. Manter backup antes de patch mínimo.

## SUCCESS_SIGNAL
Novo subprocesso Kwai recebe legenda com domínio e sufixo exato, limite 150, função idempotente, testes sintéticos de caracteres e compilação. Fila Neon preservada.

## FAILURE_SIGNAL
Arquivo mudou durante leitura, código não compila ou formato não bate; restaurar backup e encerrar sem publicação de prova.

## TEST_VALIDITY
A função editorial pura é testada sem manipular dispositivo ou publicar. Evidência de posts reais depende de vídeo futuro verificado separadamente.
