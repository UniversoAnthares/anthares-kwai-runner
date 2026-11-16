# G3 Anthares Studio — proteção da lixeira contra cron nativo em produção
STATUS: PASS
AREA: studio-g3-trashguard-protection
DATE: 2026-11-16
JOB: studio-trashguard-20261116
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
PREVIOUS_LEASE: test-hub/findings/20261116-studio-g3-trashguard-lease.md
LEASE_STATE: RELEASED
SOURCE: anthares-wordpress PR #307 commit 56efd039e328867171a7af0908932fca5f75b3c1 (PHP diff restrito)
PRODUCTION_PATH: wp-content/plugins/anthares-studio/anthares-estudio.php
PREVIOUS_SHA256: d29cb73bfbab555c904aaa07506d55943a1da533a0cc26ad37268cc479dbb8e9
NEW_SHA256: be660f3e18bea5b227d415816098cab9c7c8f39fdaa31b31f718055f4d698243
ORIGINAL_LEGACY_SHA256: 13c3c79676bc25ead5a2b02caa15306cbdefbfaf6647fbf8a636b85ab5d906bf

## Evidence
- PHP preflight syntax PASS; PR #307 15/15 static tests PASS, QA manifest 639/639 exactly_once.
- Deploy diff: 11 lines adding `pre_delete_post` filter only; all other lines unchanged from live G3.
- Original live file has mode 600; first attempt halted safely on permissions mismatch and changed no file.
- Revised deploy preserved mode 600, atomically replaced only new plugin PHP after SHA guard, and recorded old live PHP + patch in Hostinger private storage `studio-g3-trashguard-deploy-20261116`.
- WP-CLI in live environment simulated `wp_scheduled_delete` without running real delete:
  - ANST manual filter NULL — explicit deletion remains available under permission contract.
  - ANST native cron filter false — deferred deletion blocked.
  - AEST native cron filter NULL — old plugin unaffected.
- Post counts: 71 AEST, 71 ANST, 31 ANST trash, before and after. `anst_writes_enabled=0`, `anst_trash_cleanup_enabled=0`.
- Rollback artifact and manifest retained outside public_html. Original plugin hash confirmed.
- Branch PR #307 remains draft; this was a tightly scoped safety patch deployed with explicit user instruction to conclude and reversible QA.

## Consequences
G3 cron protection complete in live pilot. G4 visual authenticated baseline remains open; G5 ACF schema still offline in PR #308. No public release, no REST writes, no change to /estudio, /studio remains private.
