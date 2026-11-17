# Studio G4 PR316 — código Python/PHP e manifesto QA aprovados no checkout isolado

STATUS: PROVEN
DATE: 2026-11-17
AREA: anthares-studio/g4/independent-static-qa
JOB: studio-g4-pr316-readonly-code-qa-20261117
COMMIT: cc9f0d07cb7e4d2338d4da9b640c901b88ffe74c
SUPERSEDES: test-hub/findings/20261117-studio-g4-pr316-independent-qa-running.md
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/316

## Evidência decisiva
- Clone temporário independente da PR316 na Hostinger, HEAD idêntica a GitHub e git ls-remote.
- Python 3.6.8: `python3 -B -m unittest discover -s anthares-studio/tests -p test_*.py -v` — Ran 66 tests in 0.014s; OK; UNIT_EXIT=0.
- PHP 8.3.36: lint de quatro arquivos PHP do Studio — 4/4 PASS, LINT_EXIT=0.
- Manifesto: QA_MANIFEST_PREFLIGHT=PASS auditable=665 assigned=665 exactly_once=yes.
- Orquestrador de QA: onze itens PASS, ORCHESTRATOR_EXIT=0.
- FINAL_EXIT=0; job Anthares Remote 0d4c582f5fe6e064ca09cd225673f693, encerrado com exit_code 0.
- Clone efêmero apagado por trap EXIT; `find ... studio-pr316-qa-*` vazio (job 4c213175700326c035e563164e086b95).
- Nenhuma alteração no código da PR316 sob lease G4 de outro agente, na produção, em banco, no plugin antigo ou em opções.

## Limites
Homologada a suíte de código do commit. Sem execução de mutações REST reais, UI autenticada desktop/mobile, restauração de backup posterior ao deploy ou liberação de merge. G4 continua funcionalmente pendente; resultado deste teste não altera esse gate.
