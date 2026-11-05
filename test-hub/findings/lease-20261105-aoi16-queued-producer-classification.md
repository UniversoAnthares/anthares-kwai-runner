# AOI #16 — lease de classificação de incidentes anteriores ao envio
STATUS: RUNNING
AREA: qa-p0-incident-taxonomy-queued-and-producer
DATE_UTC: 2026-11-05T01:29:32.434Z
EXPIRES_UTC: 2026-11-05T01:59:32.434Z
OWNER: chatgpt-aoi16-20261105-incident-taxonomy
BASE_HEAD: ac7711074981ddf29e7fbcc82d6456a553c3f8ed
ITEMS: [16]
SOURCE_BLOB: tools/cortes_qa_p0_router.py 5fac1d649fb39df7ca5ec29d6814faecfc8de779
TEST_BLOB: tests/test_cortes_qa_p0_router.py 5825b58f7c94559c677889a9dd0dadb2c87622e5
PEER_CHECK: GitLab project 87307248 main has divergent blobs aa6a02a3f1012529e8ee0b470d00186e6f255bf4 and 4cd6d924fd086cf6e2abdbc024b4af809c7ff00d; no peer writes or merges.
BASELINE_PROVEN: 56 open QA-P0 issues have stage github_actions_queued_stale, i.e. job had not started, and 11 have P0_DAILY_PRODUCER_ZERO_MASTERS, explicitly stating Kwai enqueue zero is insufficient proof of absent producer or post. Existing parser labels both with publication-failure. User PC not runner; watchdog/controller/executor workflows disabled_manually.
FAILED_AVOIDED: no CI dispatch or remote publication, no deletion of issues, no closing P0, no change to quota, no old GitLab ref writes, no source or ref overwrite.
SUCCESS_SIGNAL: future queued/producer stages retain QA-P0 urgency but are classified as infra/production diagnostics without publication-failure; real publisher failures keep both labels and no blind retry.
FAILURE_SIGNAL: source refuses new P0, fingerprints change, labels for real publication disappear, issue metadata/notifications overwritten or old workflows reactivated.
TEST_VALIDITY: isolated function-level unit tests; full CI not eligible under current Actions reduction.
SCOPE: source + tests + append-only Test Hub; existing historical issues metadata only after per-issue causal readback and exact stage/fingerprint.
