# Brevo Marketing — contratos offline homologados
STATUS: PROVEN
AREA: email
DATE: 2026-11-18
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/44348290325
JOB: 134956605513
COMMIT: 295f71772f751a9e7297aad9daa3863b9dfaed31
SUPERSEDES: 20261118-brevo-marketing-gated-implementation-running.md

## Objetivo
Comprovar em CI isolado o adaptador Brevo Marketing, proteção de autorizações, persistência local piloto, bloqueio de campanhas com conteúdo alterado e comportamento após resultado incerto.

## Resultado
PROVEN apenas para contratos simulados: 16/16 testes Brevo novos, 9/9 testes de regressão do core e py_compile aprovados. Código em PR draft #2656, branch feat/brevo-marketing-gated-20261118, sem merge ou deploy de produção.

## Evidência decisiva
- Log do job: `Ran 16 tests in 0.061s` seguido de `OK`.
- Log de regressão: `Ran 9 tests in 0.001s` seguido de `OK`.
- Testes específicos passaram: `test_remote_content_change_blocks_dispatch`, `test_dispatch_ambiguous_provider_result_never_retried` e `test_ledger_draft_write_gate_preserves_staged_state`.
- CI usou `BREVO_API_KEY=''`, `BREVO_LIVE_SEND_ENABLED=0` e transporte fictício; nenhuma chamada real à API Brevo nem envio a terceiros.

## Consequência
Próximo passo: revisar PR e integrar executor externo/secret autorizado, lista qualificada com supressões e interface autenticada de aprovação, depois teste controlado autorizado em sandbox. Manter todos os switches desativados e campanha de pastores não aprovada até decisão do titular. Não confundir resultado simulado com entrega real. A fila SQLite piloto é single-writer e exige substituição por storage compartilhado se forem habilitados workers concorrentes.
