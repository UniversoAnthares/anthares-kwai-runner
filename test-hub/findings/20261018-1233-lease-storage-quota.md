# Cloudflare storage quota causal fix
STATUS: RUNNING
AREA: cloudflare-control, queue
DATE: 2026-10-18
EXPIRES: 2026-10-18T13:03:00Z
BASELINE_PROVEN: live Wrangler tail exception Exceeded allowed rows written in Durable Objects free tier. Consumer fixed native preflight now succeeds but lease1101; cleanup same500. Public health200 only proves worker alive. Publisher-target-v17 constructor unconditionally rewrites every default-account legacy row on each initialization, even when computed value remains default.
FAILED_AVOIDED: no repeated deployment/cleanup/publication attempts without causal change; no new queue or paid plan; preserve all uncertain/current jobs. Other active lease44aea25 explicitly excludes CORTES/queue.
SCOPE: eliminate no-op migration writes, report quota as503, consumer circuit backoff and automatic resume, ownership-independent deployment receipt. Existing account quota cannot be increased by code. No fee authorization, no media deletion.
SUCCESS_SIGNAL: unit test unchanged legacy accounts issue zeroUPDATE; deployed signed lease returns explicit quota503 instead of1101; correct failure receipt persists even when deploy patches dirty checkout.
FAILURE_SIGNAL: generic500, duplicate publication, deleted active/uncertain job or falsely claiming queue writes available.
TEST_VALIDITY: hub44aea25 baseline; fresh target and peer reads. Partial until actual queue writes permitted again.
