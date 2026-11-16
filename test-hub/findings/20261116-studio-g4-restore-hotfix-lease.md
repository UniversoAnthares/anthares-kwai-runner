# Lease G4: publicação controlada de correção de restauração ANST
STATUS: RUNNING
AREA: studio-g4-restore-hotfix
START_UTC: 2026-11-16T18:04:00Z
EXPIRES_UTC: 2026-11-16T19:04:00Z
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-g4-restore-hotfix-20261116
SOURCE: anthares-wordpress PR #310 SHA dbf739b32ddd3e8f6cbb11f98f196713fd1d8612
PRODUCTION_EXPECTED: new PHP SHA be660f3e18bea5b227d415816098cab9c7c8f39fdaa31b31f718055f4d698243; original legacy PHP SHA 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf.
PROOF: G4_FUNCTIONAL_PASS via MariaDB restored, 16 unit tests, QA manifest 639/639, REST owner isolation, Quill, trash/restore, write gate.
SCOPE: Only modify live anthares-studio/anthares-estudio.php using an exact single-hunk patch with GitHub/SHA guards; save previous original bytewise in Hostinger private dir, preserve mode 600, atomic rename, auto rollback if smoke check fails.
CHECKS: Native cron guard remains active, WordPress status restore new ANST filter returns previous publish and AEST unchanged, REST read 200 for entitled user, REST write locked 423, 71 AEST + 71 ANST posts, 31 ANST trash and private /studio intact.
PROHIBITED: ACF import/apply in production, editing original plugin/CPTs/posts, changing page status or auth, changing JS/CSS, merging draft PR.
CLEANUP: Remove only temporary repo clone under Hostinger private storage after test; keep rollback backup securely.
