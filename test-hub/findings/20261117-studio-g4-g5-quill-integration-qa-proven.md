# Studio G4/G5 Quill e CPTs — QA da integração

STATUS: PROVEN
DATE: 2026-11-17
AREA: anthares-studio/integration/g4-g5-quill
JOB: studio-g4-g5-quill-integration-20261117
RUN: https://github.com/UniversoAnthares/anthares-wordpress/pull/320
COMMIT: ea8205a9e7ef715cb158b22ea4b9aa55ed682f0b
SUPERSEDES: test-hub/findings/20261117-studio-g4-g5-quill-integration-running.md

## Código integrado
- Base PR316 HEAD cc9f0d07cb7e4d2338d4da9b640c901b88ffe74c.
- Proteção de erro de importação Quill: Delta preservado, autosave bloqueado, preview leitura (PR319).
- Regressão Quill em test_g6_fixed_navigation.py (PR319).
- CPTs privados com show_ui=true, capacidades manage_options, public=false e show_in_rest=false (PR317).
- Testes G5 de capacidades com fixture PHP executável compatível com Python 3.6 (PR317).
- QA Python/PHP do Studio no workflow manual existente (PR317).
- PHP da PR316 preservado exceto bloco de registro CPT. Cinco arquivos alterados, sem caminhos novos.

## QA Hostinger — clone efêmero HEAD exata
- Job 86fdb8bfdc93d0d8427c73d01875bcef, exit_code=0, REMOTE_EXIT=0.
- Python 3.6.8: Ran 69 tests, OK — 69/69 PASS.
- PHP 8.3 lint: quatro arquivos, 4/4 PASS.
- QA_MANIFEST_PREFLIGHT=PASS auditable=665 assigned=665 exactly_once=yes.
- QA orchestrator: 11/11 PASS.
- Clone temporário removido (find pr320-* vazio), job 984af70c2e53e91442e5820bfbdfe2cc.
- Plugin legado SHA256 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf preservado.
- ACF runtime OFF em produção.

## Limites
PROVEN refere-se exclusivamente ao QA de código integrado. G4/5/6 em produção, G7 de 188 requisitos e G8 final dependem de operações de escrita REST autenticada, UI desktop/mobile, capacidades WordPress reais, migração ACF e implantação com rollback. PR #320 permanece DRAFT e não deve ser mesclada/implantada sem gates. Bloqueios explícitos de ferramentas para mutação REST e aba autenticada respeitados.
