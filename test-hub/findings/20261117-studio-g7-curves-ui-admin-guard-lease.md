# Lease G7 — visualização de curvas e gate de escrita
STATUS: RUNNING
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
DATE: 2026-11-17
AREA: anthares-studio/g7/curves-private-ui-and-write-guard
SOURCE: UniversoAnthares/anthares-wordpress, ad20db193775c1693fa41819da69ac82f32663f1
NEW_BRANCH: feat/studio-g7-curves-ui-admin-guard-20261117
PEER: GitLab project 87361776, G7 source branch absent (404).
POLICY: anthares-governance REGRAS-OBRIGATORIAS.md blob 821bdcb8d8479b0c28371a6f058b4b32d86a3fa1; INDICE.md a4ae3b20fd2a07e97d75825acfe8f2a77beb0caf.
SCOPE: isolado somente na branch G7 nova; fortalecer permissões privadas de escrita G7 e implementar visualização SVG das curvas com dados reais do endpoint já existente; testes e documentação; preservar Quill, ACF OFF, CPTs do legado.
PROHIBITED: Hostinger production changes to G7, activation of ACF, public visibility, payments, Runas, bypass of denied CRUD/browser authenticated security, merge without QA.
GATE: PHP lint, Python tests, QA manifest, UI unit via JS V8. Explicit source ownership, expected base SHA, private backup.
ROLLBACK: abandonar a branch isolada; nenhuma alteração de produção esperada.
