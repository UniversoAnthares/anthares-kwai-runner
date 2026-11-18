# Studio G5 — migração ACF idempotente
STATUS: RUNNING
AREA: anthares-studio/production/acf-migration
DATE: 2026-11-17
OWNER: ChatGPT CURSO ESCRITA CRIATIVA
JOB: anst-g5-apply-20261117
BASELINE_PROVEN: ambiente Hostinger, WordPress 71 anst posts, source meta 413, fingerprint 395eb2d6be445121283d9fd92735f5e86f7239743165f9197eb9312242f1c488; 414 ACF alvos preexistentes; backup restore PASS.
FAILED_AVOIDED: nenhuma mutação REST autenticada ou navegador negado, migração pelo comando WP-CLI autorizado que exige source fingerprint, lock, transação e rollback.
SUCCESS_SIGNAL: migrador ACF_APPLY_VERIFIED e flags restauradas ao valor anterior.
FAILURE_SIGNAL: ACF_G5_HALTED; transação rollback, opções restauradas, nenhuma ativação runtime.
TEST_VALIDITY: migrador faz comparação campo a campo; não equivale a homologação UI.
LEASE: 30 minutos máximo, apenas migração G5, nenhuma alteração em projeto legado, sem PR nova.
