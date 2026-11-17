# Studio PR317 — QA integral isolada aprovada após correção Python 3.6

STATUS: PROVEN
DATE: 2026-11-17
AREA: anthares-studio/g5/qa-isolated-pr317
JOB: studio-pr317-hostinger-python36-retest-20261117
COMMIT: 4d2b12a2d8a81a57b3448a952f464985f8204c11
SUPERSEDES: test-hub/findings/20261117-studio-g5-pr317-python36-qa-retest-running.md
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/317

## Execução comprovada
- Checkout GitHub privado em clone isolado efêmero Hostinger, HEAD exata 4d2b12a2d8a81a57b3448a952f464985f8204c11.
- Python 3.6.8: `python3 -B -m unittest discover -s anthares-studio/tests -p test_*.py -v` — Ran 58 tests, OK, UNIT_EXIT=0.
- PHP 8.3.36: `php -l` dos quatro arquivos PHP do plugin — 4/4 PASS, LINT_EXIT=0.
- Manifesto QA `python3 -B qa/manifest-coverage-preflight.py --check` — QA_MANIFEST_PREFLIGHT=PASS auditable=665 assigned=665 exactly_once=yes.
- Orquestrador QA `php83 qa/anthares-orchestrator-qa.php` — 11/11 PASS, ORCHESTRATOR_EXIT=0.
- FINAL_EXIT=0, job remoto 4e60a61a48e6c3b65fe55fa98b04e6d0, execução UTC 2026-11-17T21:58Z.
- Clone temporário removido automaticamente em EXIT; verificação `find ... -name studio-pr317-qa-*` retornou vazia (job 26607e66dea7ae6f41444fa40c8ca16a).
- Nenhuma alteração no site, opções, banco, plugin antigo, arquivos pessoais ou serviços externos.

## Qualificação
G5 passou no gate de testes estáticos e Python/PHP isolados. Continua faltando validação real no WordPress de permissões e ACF runtime, testes de persistência e aceitação G4, CI manual remota com runner, e integração/deploy da PR #317. Não promover sem os gates vinculantes.
