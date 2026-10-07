# Bloqueio — check `mirror` sem `GITLAB_MIRROR_URL`
STATUS: BLOCKED
AREA: architecture
DATE: 2026-10-07
RUN: 37647378915
JOB: 112881569922
COMMIT: b6533cf4ee64f658fcbac1d79b7ed84a7eb93f0e
SUPERSEDES: none

## Baseline
O PR https://github.com/UniversoAnthares/anthares-kwai-runner/pull/3 abriu o workflow `mirror`. O job `Mirror all refs to GitLab` terminou com falha antes de qualquer push porque o log mostra:

```text
test -n "$GITLAB_MIRROR_URL"
GITLAB_MIRROR_URL:
Process completed with exit code 1.
```

O clone mirror e o `git push --mirror` não foram executados.

## FAILED_AVOIDED
Não inventar URL do GitLab, não inserir secret no repositório, não alterar o workflow para esconder a falha, não fazer push manual no GitLab e não reiniciar o job sem corrigir a configuração.

## SUCCESS_SIGNAL
A integração autorizada fornece `GITLAB_MIRROR_URL` ao workflow; o job passa pelo teste de presença e executa o espelhamento conforme a política do repositório.

## FAILURE_SIGNAL
A variável continua vazia, o secret está ausente/inacessível ou o push mirror falha após uma configuração válida.

## TEST_VALIDITY
Falha de configuração do ambiente, não falha causal dos patches deste PR. O único dado sensível não foi lido nem exposto. A correção exige que o proprietário configure/revalide o secret/variable do GitHub Actions e a autorização do destino GitLab.

## Consequência
O PR continua aberto para revisão, mas o check `mirror` permanecerá falho até a configuração externa ser corrigida. Não rerodar automaticamente.
