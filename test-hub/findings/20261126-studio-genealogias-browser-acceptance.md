# Anthares Studio — Genealogias — homologação em navegador (26/11/2026)

STATUS: PROVEN — authenticated production functional browser acceptance.
SOURCE: UniversoAnthares/anthares-wordpress PR #435.
EVIDENCE: WinRemote task d5567bbf2e6c, BROWSER_QA_PASS=21, QA_CLEANUP_OK children=5 session_revoked=1.
Chrome isolated authenticated context, desktop 1440x1000 and mobile 390x844. Passed: navigation, tree creation, canonical character creation, automatic edits, filiation, union, portrait, cycle rejection, kinship, search, chronology, orientation, zoom, SVG opened in Chromium, PDF opened with pypdf, persistence after reload, multiple trees, character reuse, theme, responsive layout, zero uncaught JS errors.
The prior two harness assertion failures were corrected without changing production. Prior 33 transactional checks passed. Temporary test records removed and session revoked. No separate physical-mobile-device test or manual screenshot comparison. Two previously identified unrelated JSON restoration failures remain outside this acceptance.
