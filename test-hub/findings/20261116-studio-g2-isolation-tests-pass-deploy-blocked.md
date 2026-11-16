# Anthares Studio — isolamento em branch validado, deploy bloqueado
STATUS: PARTIAL
AREA: studio-g2-isolation-development
DATE: 2026-11-16
RUN: ambiente externo Hostinger, WordPress CLI, Python unittest e PHP QA
JOB: g2-isolation-branch-validation-20261116
COMMIT: anthares-wordpress/e6366080123f467baaffc9fc3778509b0f093bb7
SUPERSEDES: test-hub/findings/20261116-studio-g2-snapshot-proven-isolation-lease.md

## Resultado PROVEN (código de isolamento)
- PR #303 (draft): snapshot literal `c11c19a5826c2bf74c9e42c2ce1498a8b6f0f4b4`, 7 arquivos byte a byte equivalentes à instalação Hostinger.
- PR #304 (draft): branch `feat/studio-g2-isolated-runtime-20261116`, base snapshot #303, commit `e6366080123f467baaffc9fc3778509b0f093bb7`.
- Funções, CPTs, metadados, cron e opções independentes via `anst_*`; REST `anthares-studio/v1`; shortcode `[anthares_studio]`; página-alvo `/studio`.
- JS modificado apenas para nomes de CPT onde indispensável; markup, classes CSS `aest-*`, DOM root, Quill e cinco arquivos de assets preservados byte a byte; filtro de entitlement antigo permanece compatível.
- `python3 -m unittest discover -s anthares-studio/tests -v`: 5/5 PASS.
- `php -l`: PASS.
- `python3 qa/manifest-coverage-preflight.py --check`: PASS, auditable=637 assigned=637 exactly_once=yes.
- `php qa/anthares-orchestrator-qa.php`: 11 PASS.
- WordPress CLI com legado ativo e nova classe de funções incluída em processo isolado: PHP_FUNCTION_NAMESPACES=PASS; REST_HOOKS_COEXIST=PASS; CPTS_INDEPENDENT=PASS; ORIGINAL_COUNTS_UNCHANGED=71; NEW_POSTS=0; WPCLI_COEXISTENCE=PASS.
- A verificação inicial de rota HTTP via `wp eval-file` registrou rotas antigas e não as novas porque `rest_api_init` já havia sido executado antes do `require` manual. Essa execução tardia limita o harness, sem demonstrar falha do registro do plugin. HTTP de nova REST ainda NÃO HOMOLOGADO.
- Verificação de produção após teste: `/estudio` HTTP 200, `/studio` HTTP 404, diretório plugin novo ausente; hash PHP original `13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf`.

## FAILED_AVOIDED
- Plugin original sem alterações; novo plugin permanece apenas no GitHub, sem deploy ou ativação.
- Preservadas todas as 71 entradas do CPT original; nenhum `anst_*` novo criado.
- Não interpretar inicialização tardia do REST no WP-CLI como falha de rota; teste HTTP completo ainda pendente.
- QA JS Node ausente no Hostinger, registrar `NODE_JS_CHECK_UNAVAILABLE` sem inferir aprovação sintática por Node.

## Pendências / consequência
- G0: documentação mesclada #302 e testada.
- G1: backup restaurado, equivalência visual/prints completa ainda PENDENTE.
- G2: código isolado em #304 DRAFT, precisa teste real de REST e telas em staging após G1; **bloqueado merge/deploy/ativação**.
- G3+: migração de dados e normalização ACF só após paridade e gateways aprovados.
- Este registro encerra o lease de desenvolvimento de isolamento nesta sessão. Novo trabalho mutável exige lease novo e baseline fresco.

## Evidência
GitHub: https://github.com/UniversoAnthares/anthares-wordpress/pull/303
GitHub: https://github.com/UniversoAnthares/anthares-wordpress/pull/304
Dados e restauração: test-hub/findings/20261116-studio-g1-backup-restored-visual-open.md.
