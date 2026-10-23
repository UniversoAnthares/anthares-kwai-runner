# Lease: replace ACF PRO with Anthares-owned compatibility plugin
STATUS: RUNNING
AREA: wordpress-security
DATE: 2026-10-22
OWNER: chatgpt-gpt6
LEASE_EXPIRES_UTC: 2026-10-23T03:55:00Z
BASELINE_PROVEN: Hostinger 12 ACF field groups and 33 fields using only free types post_object/range/text/textarea/true_false, ACF free 6.8.10 active; ACF PRO 5.10.2 active; WP CLI shadow boot without PRO loaded all 12 groups and 33 fields.
FAILED_AVOIDED: no direct DB migration or rewriting proprietary ACF source; do not deactivate paid plugin without a validated free fallback and verified private backup; no mass edits to field values.
SUCCESS_SIGNAL: self-owned Anthares Fields plugin installed; Pro inactive; free ACF 6.8.10 loaded in real WP; all 12 groups/33 fields retained and UI available; site 200, integrity regressions pass, rollback saved.
FAILURE_SIGNAL: fields disappear, front-end fatal, missing dependency, missing confirmation.
TEST_VALIDITY: WP CLI read-only inventory is not field-write test; do not claim actual admin UI full manual QA without evidence.
