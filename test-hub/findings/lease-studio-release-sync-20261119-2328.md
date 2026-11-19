# Lease — sincronização segura do código Anthares Studio, 19/11/2026
OWNER: ChatGPT / STUDIO_SYNC_MAIN_TO_HOSTINGER_20261119_2328
STATUS: ACTIVE
SCOPE: atualizar somente anthares-studio/anthares-estudio.php, anthares-studio/assets/estudio.js e anthares-studio/includes/acf/class-anst-acf-repository.php em Hostinger para o código já integrado ao GitHub main.
START_UTC: 2026-11-19T23:28:00Z
EXPIRES_UTC: 2026-11-19T23:58:00Z
GITHUB_MAIN_PIN: 075e525780064340f28eceb59b128ef4de5f13c8
HOSTINGER_BASELINES: PHP c166c7d2fb0c65b18c99d937ae07d7fbbc20b5d1947d804f639b7a0d80dc6de1; JS 58c19bf313cbc9ebfe6501cd78d25f5cf95e8421bb9d7392ca3fa00bd3b53228; ACF 4dd6eee9f484bd95ddc55e00bed7f7f210569bbbf7a3b9dfe43a722e36db225a.
BASELINE: main has safe additional chapter-move action, corrected Portuguese text and documentation comments absent in deployed plugin; 116/116 source tests PASS; PHP lint PASS. Main CSS/assets besides the three paths match production. 9 documentation/test-only files exist in main but do not require production deploy.
RISKS: avoid changing old /estudio; avoid changes to user content and database; preserve concurrent agents and settings; refuse if any SHA or pinned HEAD changes. Snapshot originals privately and roll back only files owned by this lease if testing fails.
SUCCESS: exact SHA equality main/Hostinger for three runtime files, PHP lint, JavaScript parse, Python tests and HTTP /studio 200 without errors. Existing privacy/publication options unchanged.
FAILURE: any mutation by peer or incompatibility requires abort/reconcile, no blind overwrite.
