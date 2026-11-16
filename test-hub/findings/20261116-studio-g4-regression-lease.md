# Lease QA funcional G4 do Anthares Studio
STATUS: RUNNING
AREA: studio-g4-backend-regression
START_UTC: 2026-11-16T17:55:00Z
EXPIRES_UTC: 2026-11-16T18:55:00Z
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: g4-backend-isolated-20261116
GOVERNANCE: anthares-governance REGRAS-OBRIGATORIAS.md SHA 821bdcb8d8479b0c28371a6f058b4b32d86a3fa1
BASELINE: anthares-estudio SHA256 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf; anthares-studio SHA256 be660f3e18bea5b227d415816098cab9c7c8f39fdaa31b31f718055f4d698243; snapshot sha256 26369c846d50ca691bf53423171a385cc7fe782b829f401a4bf859fff230b688
PERMITTED: MariaDB restored in isolated UNIX socket with skip-networking, WP core symlink and only approved plugin symlink; function/REST regression using synthetic posts within isolated DB; no external emails; create and clean temp artifacts in Hostinger private storage; static QA and owner authorization regression.
PROHIBITED: Production DB mutation, /estudio changes, public /studio, new user grants, disabling site services, exposing screenshots/author data.
ROLLBACK: Close isolated MariaDB server and remove exact owned temp directory and short socket in trap, preserving live production untouched.
ACCEPTANCE: Create/read/update user project, note, card, chapter Delta, trash/restore, cross-author rejection and flags; compare original AEST counts; log typed/filtered outcomes only. Screenshot parity remains independent gate requiring authorized browser session.
