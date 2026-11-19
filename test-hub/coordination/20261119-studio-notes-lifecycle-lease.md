# Studio notes lifecycle — lease
OWNER: ChatGPT / studio-notes-lifecycle
STATUS: RUNNING
DATE: 2026-11-19
CODE: UniversoAnthares/anthares-wordpress fix/studio-notes-lifecycle-20261119
SCOPE: editar anotações existentes, vincular/desvincular ideias globais, preservação do ID, CAS de versão e isolamento por proprietário.
BASE: WordPress 4f7a01c9a80ab8cde980f1b08f8d30c87003f5e8
CONSTRAINT: exclusivamente plugin anthares-studio e teste existente; preservar /estudio/ e dados reais.

STATUS: COMPLETED
EVIDENCE: PR #350 merge 11636113d40ffa6e677536db24f2ca35a339ce63; 103 tests PASS, PHP/Bun PASS, notes edit and reassignment endpoint matched installed live code; CSS editor deployed on Hostinger with backup private.
