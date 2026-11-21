# Studio Items 8 + 9: Narrative timeline and Hero Journey
OWNER: ChatGPT / STUDIO_NARRATIVE_8_9_20261120
STATUS: CLOSED_SUCCESS
SOURCE: PENDÊNCIAS URGENTES.md 8/9, especificacao_atualizada.md IDs 059/060/092/139/180, PLANO MESTRE B15, user specifications in current conversation.
TARGET_REPO: UniversoAnthares/anthares-wordpress
START_HEAD: 4407f0f7f575d1867525e4d6101b865b6061bd7b
TARGET_BRANCH: feat/studio-narrative-timeline-journey-20261120
SCOPE: preserve Chapter CPT, existing structure map, event/cena canonical ACF entity IDs; two orders; manual chronology, relative relations, timeline stages, manuscript-context warning, drag chapter to stages.
SAFETY: no third simultaneous-comparison mode; chapter creation remains free; no change to /estudio; private author rights; optimistic revision; production rollback.
STATUS_VERIFY: PHP/JS and transactional QA; editor/real-user visual QA only when authenticated browser accessible.

END: 2026-11-20 (America/Campo_Grande)
IMPLEMENTATION: Anthares WordPress PR #395 (merge 643c1218233c3012e091142a9f58356c2050bf68); temporal refinement PR #396 (merge afdfb42930a3c97762ea4053c064ba6c5cdc34e1).
QA: WordPress live plugin loaded; 26/26 transacted checks PASS and ROLLBACK=EXECUTED. PHP 8.3 lint and JS node --check PASS; QA coverage 740 source files, zero missing/duplicate, manifests identical.
LIVE: /studio/ HTTP 200; /estudio/ HTTP 200; timeline JS/CSS HTTP 200; active plugin. Six plugin-file hashes verified matching main. Backups stored privately outside public_html at studio-private-backups/20261120-items8-9/ including relative-intervals/.
USER_CONTRACT: Manifesto badges only after chapter classification starts; inline Manuscrito assignment; scenes and summary events can have independent stages; two separate order modes; no simultaneous comparison view; 12 stages can be re-ordered or hidden reversibly; historical date, relative offsets and free chronology rank.
FINAL_STATUS: Items 8/9 implementation deployed. Browser-visual authenticated walkthrough remains item 21 operational QA.
FINDINGS: test-hub/findings/20261120-studio-narrative-items8-9.md
