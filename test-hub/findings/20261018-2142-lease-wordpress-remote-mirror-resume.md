# Resume isolated Browser and independent WordPress mirror
STATUS: RUNNING
AREA: ara-control, browser-session, wordpress-mirror
DATE: 2026-10-18
LEASE_OWNER: codex-01a14ef0
LEASE_EXPIRES_UTC: 2026-10-18T22:12:00Z
SUPERSEDES: 20261018-1223-lease-remote-browser-wordpress-mirror.md
BASELINE_PROVEN: ARA recovery commit8a08de61, Cloudflare gateway version85ef5239-02ac-4eb2-9ab2-842d7e422b3e; fresh session_status connectedtrue with empty queue and capabilities authenticated. Browser dedicated profile retains GitHub auth and GitLab login via existing GitHub authorization. WordPress GitHub4e24f527, GitLab4cdde49; only CI YAML differs. GitLab received recent AutoSync commits from an as-yet-unidentified executor.
FAILED_AVOIDED: no repeat of stale device token rotation; no personal browser profile, no competing automatic writer activation before identifying existing AutoSync. No paid service, no forbidden provider.
SCOPE: restricted project credential, safe remote WordPress mirror/scheduler, Browser persistence/recovery and final ARA proof. No anthares-clipper, CORTES, Android executor/queue changes, reboot or logoff. Existing broad storage/Android leases are separate.
SUCCESS_SIGNAL: durable authenticated browser, least-privilege project credential stored only in secret managers, automatic remote sync preserving every exclusive file/history, checkpoint/idempotence/concurrency/recovery proof.
FAILURE_SIGNAL: unresolved content conflict, stale destination, competing writer, missing actual scheduled-run evidence.
TEST_VALIDITY: fresh HEAD/blob/peer reads; preserve GitLab-only CI. Do not report a manual run as scheduler proof. GitHub running runs inspected; no same-chain live experiment found.
