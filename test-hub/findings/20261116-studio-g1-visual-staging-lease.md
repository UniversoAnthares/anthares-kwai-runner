# Lease G1 baseline visual e G2 homologação isolada do Studio
STATUS: RUNNING
AREA: studio-g1-visual-staging
DATE: 2026-11-16
START_UTC: 2026-11-16T16:08:00Z
EXPIRES_UTC: 2026-11-16T17:08:00Z
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-visual-baseline-and-isolated-validation-20261116
COMMIT: anthares-wordpress/main=40820c15388f584beca830feec3200a135833b28; isolated PR #304=e6366080123f467baaffc9fc3778509b0f093bb7
SUPERSEDES: test-hub/findings/20261116-studio-g2-isolation-tests-pass-deploy-blocked.md

## Baseline
- 19 docs G0 merged PR #302 and verified by QA; 7 legacy files snapshot PR #303 and isolated PR #304 are unmerged DRAFT.
- Backup of WordPress DB and original plugin restored in MariaDB isolated: 217 tables, 40 published, 31 trash, 7 Delta; sha256 and source PHP baseline confirmed.
- /estudio/ 200, /studio/ 404, clone plugin not installed as of 16:06 UTC.
- 5 unit tests isolation PASS and 637/637 manifest QA PASS, WordPress CLI coexistence 71 legacy entries unchanged.
- G1 screenshot parity incomplete; G2 full runtime route and UI tests incomplete; no authorization to skip these controls.

## Allowed actions
- Inspect and capture original authenticated screens remotely with hidden session, staging artifacts exclusively outside personal PC and public_html.
- Prepare isolated staging / or pilot admin-only /studio when safe, with feature gate OFF for all writes until proof, complete per-step checks, rapid rollback; any activation on live WordPress requires reconciliation and no original impacts.
- Write tests, migration dry run and documentation in dedicated branch/PR with current SHA and peer checks.
- With successful proof, import only isolated ANST data, preserving AEST originals, no outbound emails/payments.
- No new CDN, storage provider, price, or paid quota.

## Prohibited
- Editing original anthares-estudio files/posts/meta.
- Deploying unreviewed code or merging the raw snapshot before G1 visual approval.
- Refactoring HTML/CSS/ACF before proving parity; global database restore; exposing private contents to public screenshots/logs.
- Moving user's personal browser, mouse, keyboard or window to perform tests.
- Declaring completion from status 200 or lint only.

## Success and rollback
- Screenshots and test outcomes private, sanitized; legacy SHA unchanged.
- Verified staging paths and data isolation; REST permissions checked; G1/G2 acceptance documented.
- If any step fails, deactivate only new plugin and remove page if owned by this job after verifying ownership; keep copy and backup.
- Each state transition recorded in append-only finding, lease closed by final finding.
