# AOI #16 — lease de retificação conservadora de metadados QA P0
STATUS: RUNNING
AREA: qa-p0-issue-metadata-queued-and-producer
DATE_UTC: 2026-11-05T01:33:10.952Z
EXPIRES_UTC: 2026-11-05T02:03:10.952Z
OWNER: chatgpt-aoi16-issues-20261105
BASE_MAIN_HEAD: 99d276a8b1900cd882cf95d7375d9eb7cb564032
ITEMS: [16]
SOURCE_PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2106
BASELINE_PROVEN: GitHub search showed 56 open issues with exact stage github_actions_queued_stale, 11 with P0_DAILY_PRODUCER_ZERO_MASTERS; all previously carried misleading publication-failure. Prior AOI16 32 visibility issues reclassified in closed lease 20261104-aoi16-32-infra-p0-reclassified-lease-closed.md, no overlap of stage.
FAILED_AVOIDED: no issue closure, no lost fingerprint/evidence/comments, no rerun/republish/queue edit, no provider auth bypass, no Actions reactivation. Controller/watchdog/executor workflows disabled_manually, event listener on issues only opened/reopened/labeled; removal of publication-failure sends unlabeled event, excluded.
SUCCESS_SIGNAL: exact stage/fingerprint validated individually before metadata change; title and labels accurately distinguish infra/producer; original open state and all original comments preserved. All true publisher incidents remain unchanged.
FAILURE_SIGNAL: any stage mismatch, changed issue content or concurrent mutations => skip, no blind retry.
TEST_VALIDITY: labels/title/body readback on GitHub, read-only public evidence and exact current issue state; no publication.
SCOPE: only prepublication QA-P0 issue metadata, separate from canonical source already merged in PR2106. Audit all changed issue numbers.
