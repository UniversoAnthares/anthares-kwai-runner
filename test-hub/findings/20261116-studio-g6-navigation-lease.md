# Lease G6 — navegação estável e regressão do Anthares Studio
STATUS: RUNNING
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
AREA: studio-g6-navigation
START_UTC: 2026-11-16T19:55:00Z
EXPIRES_UTC: 2026-11-16T21:00:00Z
BASE: UniversoAnthares/anthares-wordpress feat/studio-g5-acf-runtime-adapter-20261116 SHA 3fb80a53e087ef8d0bc9d8f88ffa46a0f3d3dae6
CONTRACT: CONTRATO_NAVEGACAO_FIXA_ESTUDIO_ANTHARES.md v2.0
GOVERNANCE: REGRAS-OBRIGATORIAS.md SHA 821bdcb8d8479b0c28371a6f058b4b32d86a3fa1
OWNED: isolated branch / anthares-studio/assets/estudio.js / CSS additions if needed / new tests/doc / QA manifests.
ALLOW: implement exactly 5 global menu entries, 7 stable project groups, nested planning tools, breadcrumb, contextual trash action; old functionality/routes backward compatible, no new payments, preserve original plugin and UI baseline.
BLOCK: no production deploy, no public release, no ACF live, no touching original; visual G4 authenticated screenshots prerequisite to promotion/merge, maintain PR draft.
TEST: JS parsing, static assertions, no dead buttons, navigation route compatibility, responsive CSS, QA coverage; add isolated test if authenticated login available legitimately.
ROLLBACK: drop draft branch; production unaffected. Avoid creating any user data or background task.
