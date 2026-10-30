# CORTES — corrigir a fonte do preflight hospedado
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-30
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41105474016
JOB: 124233983460
COMMIT: pending
SUPERSEDES: 20261030-cortes-clipper-hosted-readiness-running.md

## BASELINE_PROVEN
- O workflow hospedado em runner público Ubuntu conseguiu autenticar e clonar o GitLab privado no run 41105474016.
- O teste real falhou com CORTES_HOSTED_SOURCE_FILE_MISSING. O GitLab espelhado não contém os módulos CORTES atuais do GitHub canônico.
- O repositório público já usa um fluxo de leitura autenticada do GitHub privado a partir de GITHUB_MIRROR_TOKEN do projeto GitLab autorizado no workflow `cortes-phase4-regular-fallback-once.yml`.
- `cortes-daily.yml` e `cortes-short-resume.yml` seguem ativos em Windows e possuem checkpoint em D:; esta prova não autoriza sua retirada.

## FAILED_AVOIDED
- Repetir a clonagem do espelho privado incompleto.
- Publicar, renderizar, iniciar filas ou copiar credenciais para logs/artifacts.
- Alterar os produtores antes da prova de source, quota, ledger externo, e fencing.

## SUCCESS_SIGNAL
- `CORTES_HOSTED_CANONICAL_SOURCE=PASS`.
- `CORTES_HOSTED_READONLY_GATE=PASS` no mesmo job hospedado.
- Referência GitHub source SHA emitida sem credenciais e sem side effects.

## FAILURE_SIGNAL
- `CORTES_CANONICAL_SOURCE_CREDENTIAL_UNAVAILABLE`, `CORTES_GITHUB_CANONICAL_CLONE_DENIED`, `CORTES_HOSTED_SOURCE_FILE_MISSING`, `CORTES_HOSTED_MEDIA_PREFLIGHT_FAILED` ou job falho.
- Classificar cada falha pela causa observada, evitando repetir testes sem mudança causal.

## TEST_VALIDITY
Somente leitura, em runner Ubuntu público, trigger do próprio workflow no main. Confirma compatibilidade preliminar; depende ainda de ledger imutável externo e de transferência segura do controle de produção. Nenhuma mídia, credencial ou publicação pode ser alterada por este teste.
