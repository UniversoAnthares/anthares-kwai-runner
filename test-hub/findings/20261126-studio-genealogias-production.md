# Anthares Studio — Genealogias — 2026-11-26

Status: PRODUCTION DEPLOYED; authenticated visual/download QA outstanding.

- Canonical PR: UniversoAnthares/anthares-wordpress#435, merge e42c46ba55697d243cba4ab8b84582fb49093940.
- 33/33 WordPress transactional checks passed on production; rollback confirmed; post count 15360 before and after.
- 7/7 deployed file hashes match. Public JS and CSS hashes match deployed files. /studio/ and /estudio/ HTTP 200; anonymous genealogies endpoint HTTP 401.
- Legacy fingerprint unchanged: df017e095674def15a05fe0931457ea807551a19f001d0bba88b8f1a7c490b34.
- QA manifest 799/799; PHP lint and Bun browser build passed.
- Python suite 316/318; both JSON restoration failures reproduced on untouched baseline: test_complete_json_restore_preflight_and_id_integrity and test_core_recovery_in_js_vm.
- Existing ACF character and relation IDs preserved; three additive ACF groups; private project genealogy membership, graph UI, SVG/PDF export controls.
- Private Hostinger backup and CAS deployment completed. GitLab divergent mirror left untouched.
- Authenticated browser visual walkthrough and actual downloaded SVG/PDF opening remain unverified. No assertion of full end-to-end acceptance.
