# Anthares Studio — snapshot G2 comprovado; lease de isolamento somente em branch
STATUS: RUNNING
AREA: studio-g2-isolation-development
DATE: 2026-11-16
START_UTC: 2026-11-16T15:49:00Z
EXPIRES_UTC: 2026-11-16T16:19:00Z
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: isolamento sem deploy dos identificadores duplicados do Estúdio
COMMIT: anthares-wordpress/main=40820c15388f584beca830feec3200a135833b28
SUPERSEDES: test-hub/findings/20261116-1541-lease-studio-g2-source-snapshot-only.md

## BASELINE_PROVEN
- Branch `feat/studio-g2-raw-legacy-snapshot-20261116`, SHA `c11c19a5826c2bf74c9e42c2ce1498a8b6f0f4b4`; PR #303 DRAFT, sem merge nem deploy.
- 7 arquivos originais copiados byte a byte; `diff -rq` PASS; PHP original/cópia SHA-256 `13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf`.
- QA em Hostinger: 635/635 arquivos cobertos exatamente uma vez, 11 contratos PHP QA PASS, PHP lint PASS.
- Banco legado: backup e restauro isolados G1 PASS, 40 posts internos publicados + 31 na lixeira + 7 documentos Delta, sem alteração em produção.
- Captações visuais completas G1 ainda pendentes, portanto a implementação aqui é somente código em branch privada de desenvolvimento.

## FAILED_AVOIDED
- Ativar snapshot bruto simultaneamente com legado (colisões `aest_*`).
- Trocar HTML/CSS/layout e perder paridade visual.
- Divulgar CPTs privados e dados do usuário.
- Criar /studio, modificar /estudio, acionar cron ou migrar banco antes de homologação.
- Armazenar trabalho no PC, fazer merge na main, executar deploy.

## SUCCESS_SIGNAL
- Branch isolada baseada em `c11c19a`, com prefixos PHP/CPT/meta/opções/cron `anst_*` e REST `anthares-studio/v1`; shortcode próprio e enqueues exclusivos em /studio.
- HTML, estrutura Quill, JS visual e CSS preservados; testes estáticos, PHP lint, JS check, preflight QA PASS.
- PR DRAFT baseando-se na branch snapshot, proibido merge/deploy, com evidência de colisões eliminadas.

## FAILURE_SIGNAL
- Alteração do HTML/layout; fonte original alterada; uso de `aest_*` como CPT de gravação na cópia; falta de cobertura; escrita em /estudio; criação de dados anst_* no banco real.

## TEST_VALIDITY
É permitido editar somente a branch de isolamento derivada do snapshot. Não é permitida instalação nem ativação na Hostinger, criação de página, migração, mudança em dados originais ou merge na main. Auditoria de baseline visual permanece gate separado.
