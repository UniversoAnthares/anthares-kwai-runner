# QA: Kwai publisher static safety is now green; queue production still blocks canary
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37394638955 ; https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37394632606
JOB: 112047582710 ; 112047567896
COMMIT: 142f30e97b8a3c41459ecb1cdc415352846dc5ec
SUPERSEDES: none

## Resultado
A camada estática do publisher está novamente verde: seleção determinística de mídia, prepare->started->commit, verificação específica de conta/título e complete após verificação passaram. Porém o self-test de produção do control plane v13 ainda retorna HTTP 500 failure_counter_reset_failed. Portanto o canário real continua bloqueado por control-plane acceptance, independentemente da segurança estática do publisher.

## Evidência decisiva
Run 37394638955 emitiu KWAI_STARTED_BEFORE_COMMIT_STATIC_OK e KWAI_PUBLISH_SAFETY_STATIC_OK. Run 37394632606 confirmou health v13 e depois QUEUE_SELFTEST_HTTP=500 com error=failure_counter_reset_failed.

## Consequência
Não confundir o green estático com autorização para publicar. Aguardar/certificar v14 ou correção equivalente do circuit-breaker e novo /queue-self-test 200; em paralelo, kwai-login/Launcher permanece pré-condição separada.