# Lease Anthares Studio — adaptador runtime ACF em PR draft
STATUS: RUNNING
AREA: studio-g5-acf-runtime-preparation
START_UTC: 2026-11-16T18:14:00Z
EXPIRES_UTC: 2026-11-16T19:14:00Z
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-g5-runtime-adapter-20261116
SOURCE_BRANCH: anthares-wordpress feat/studio-g5-acf-migrator-offline-20261116 SHA bba7660d2705bb87d7db9605eaf408cbcc9e176d
RELATED: G4 restore filter PR #310 SHA dbf739b32ddd3e8f6cbb11f98f196713fd1d8612, live PHP SHA 477f4e2dd2fe1cc79c0f0793109c257edb212d0e16e68f68c3278d323233a7b3
PERMITTED: Modify only isolated branch new Studio PHP and new ACF include/tests/README, synchronized manifest. Replace direct postmeta calls with ACF adapter behind constant+option BOTH default OFF. Remap meta_query to studio_* only when approved. Test in isolated MariaDB with ACF migrated.
PROHIBITED: Deploy the adapter, migrate/alter ACF data in production, change /estudio or /studio private visibility, modify CSS/JS/Quill, change original plugin or production user permissions, merge draft chain to main.
SUCCESS: Runtime OFF gives same REST results as original clone including G4 restore fix; ACF runtime ON after isolated migration supports CRUD and relationships, Quill; unknown fields rejected; original source unchanged.
ROLLBACK: Drop draft branch; no production effects. Release lease upon evidence recording.
