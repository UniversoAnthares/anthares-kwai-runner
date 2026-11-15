# AGENTE 02 — Anthares Studio ACF: QA funcional isolado Hostinger
Date: 2026-11-15
Owner: ChatGPT AGENTE 02
Status: PARTIAL — offline PHP runtime PASS; production/staging ACF integration still NOT_EXECUTED

## Source and integration
- Code PR: https://github.com/UniversoAnthares/anthares-wordpress/pull/284
- Code head tested: 6f439e12209a5ac6887cb8a8f64bf7402861b15a
- Tested exact entity-adapter blob: 44292e508ad14cbfca586250cc112ba9261951cf
- Tested exact mock-runtime blob: b821efb8c1d8b8938ea94d156267a931338b76e4
- All 12 ACF Local JSON groups were copied to isolated private host staging and verified individually against GitHub blob SHA before execution.
- PR #284 merged at 2026-11-15T17:02:31Z into integration branch feat/anthares-studio-acf-20261114, merge SHA 30c6cbbd3f649f1860ee9fab534509df8bdc5c7e.
- Main PR #275 remains open/draft; this merge is not production release.

## Runtime evidence — PROVEN
- Host: authorized existing Hostinger SSH environment; used PHP /opt/alt/php85/usr/bin/php (8.5.12). Default CLI php is 7.4.33, not applicable to plugin's PHP>=8.0 requirement.
- PHP lint: includes/entities.php PASS and tests/acf-runtime-contract.test.php PASS on PHP 8.5; no syntax errors.
- Executed isolated script: php -d display_errors=1 tests/acf-runtime-contract.test.php
- Result: ACF_RUNTIME_CONTRACT=PASS; exit code 0.
- 34 assertions PASS: 12 groups, 313 keys, editable fields; allowed/denied enums; project/revision/provenance unknown field refusal; scalar validation; relationship dedup/limits; project and owner scoping; invalid IDs; single/multiple refs; global idea reference scoping; max/step number checks; invalid/valid date conversion; URL; separate chronology/order; optimistic revision conflict; foreign-owner read/create protection; missing/stale ACF schema fail-closed before post insertion.
- Command job id f7bedb96fd34e03f9a6774902bab32c3.
- Earlier failed mock invocation revealed a test-only global variable shadowing defect, fixed in code commit 6f439e1; the successful execution used that exact corrected mock.
- No WordPress database, live site, customer data, secrets or real authenticated session was accessed by the offline mock.

## Scope boundaries and cleanup
- Temporary staging was a hidden directory under the Hostinger account home, outside public_html.
- The PC served only as an SSH transport, with no agent work files stored on PC.
- Attempt to transfer the large main plugin source for additional Python static QA was blocked by an explicit tool security restriction; the transfer was stopped and not retried by an alternate route.
- Owned temporary directory was removed immediately and absence verified: AGENT02_TEMP_CLEANUP=PASS, command job 4d7baa7d925ad0e7e9082927b207ccdd.

## Still pending
- Direct execution of python3 anthares-studio/tests/acf-schema-contract.test.py and QA manifest/orchestrator preflight on a full, authorized checkout.
- GitHub Actions workflow on isolated branch was present, but no workflow run registered (observed count=0).
- Actual WordPress+ACF database writes/reads in authenticated staging, Local JSON load/save round-trip, provenance compatibility checks, owner A/B against real API, full revision/version restoration and rollback.
- Release gate: keep main PR #275 in draft and do not deploy production based solely on isolated mocks.
