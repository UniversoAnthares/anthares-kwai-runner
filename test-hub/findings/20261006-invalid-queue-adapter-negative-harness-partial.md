# Queue adapter negative matrix — PARTIAL / INVALID HARNESS
STATUS: PARTIAL
AREA: qa
DATE: 2026-10-06
RUN: 37403182354
RESULT: 3/5 valid green; version-mismatch and malformed-ack harness cases invalid.
VALID_GREEN: bad-generation, malformed-health, http-error.
INVALID: stub curl routing did not reliably distinguish calls for version-mismatch/malformed-ack, so their red jobs are not production regressions.
DECISION: do not count those two red jobs as adapter failures; replace with corrected/new isolated cases.
