# G7 lease — normalização de entidades narrativas e relações
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
AREA: studio-g7-story-domain
STATE: RUNNING
START_UTC: 2026-11-16T20:04:00Z
EXPIRES_UTC: 2026-11-16T21:10:00Z
SOURCE: anthares-wordpress feat/studio-g6-fixed-navigation-20261116 SHA 3efad7ad3b41e765132f625202daad88f8f2ee7d
CONTRACT: ANST09–12, ANST15, requisitos 046–106, 119–152 da especificação e B12–B20 do Plano Mestre.
PERMITTED: isolated G7 branch only; NEW includes/domain PHP, new ACF JSON groups ANST09–12/15, new tests and docs, isolated bootstrap require line + QA manifests. Dynamic backend data writes require opt-in existing ACF runtime and anst_writes_enabled, never enabled in production. No exposure of private content.
PROHIBITED: alter /estudio, Hostinger live plugin, /studio visibility, original Quill assets, payments/Runas, public publishing; never claim 188 requirements complete merely from CPT/API.
SUCCESS: proper IDs, project+owner checks, relation direction, no cross-owner links, WordPress CPT private, ACF fields, REST create/list/update/trash, curves sourced from actual entries; PHP lint and isolated DB regression. PR draft; publish only after G4/G5/G6 approved.
