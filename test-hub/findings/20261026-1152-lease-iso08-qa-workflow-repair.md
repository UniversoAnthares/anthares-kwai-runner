STATUS: RUNNING
OWNER: chatgpt-ops / ISO08-20261026
AREA: CORTES-ISO-08 isolated QA workflow syntax repair
LEASE_START_UTC: 2026-10-26T11:52:53Z
LEASE_EXPIRES_UTC: 2026-10-26T12:17:53Z
TARGET: UniversoAnthares/anthares-clipper, branch platform/iso08-qa-rehearsal-20261025, file .github/workflows/cortes-shadow01-readonly-qa.yml
BASELINE: clipper/main db6c12fdaa0af01e3b68b8a527b2e02c12c21837; branch blob 35da8ab53a9399bbe73d83521ce66873019462a9.
ISSUE: prior QA workflow edit accidentally truncated PowerShell regex and duplicated trailing section; fix without touching production code.
RISK_BOUNDARY: no changes to production, SQL, queues, identity, user device settings, or publishing; no bypassing a security refusal.
SUCCESS_SIGNAL: branch readback with one valid test/run + artifact step; CI only if independently authorized.
FAILURE_SIGNAL: concurrent writer, source SHA drift, provider denial.
NEXT: fix workflow in isolated branch, record exact blob and test evidence, open review PR, update canonical checklist and evidence.
