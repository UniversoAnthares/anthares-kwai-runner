# ARA item fixo 7 — medir economia efetiva de CU-horas
STATUS: RUNNING
AREA: anthares-remote / neon-idle-optimization / cu-hour-acceptance
DATE: 2026-10-28
OWNER: ChatGPT GPT-6
RUN: Direct Neon project/endpoint read-only telemetry, PG catalog and ARA session. No deployment or code mutation.
JOB: none
COMMIT: 2d28129654740aea97c1a8dd1f085658516acf29
SUPERSEDES: none

## BASELINE_PROVEN
Earlier item 2 recorded project approximately 76.98 CU-hours, later 77.20 CU-hours on Oct 28 without an exact timestamp; a 148-second DB statistics observation had 1,418 ARA job-index scans, 11 heartbeat table updates, 26 OAuth inserts, and 33 job updates. C8 agent polls legacy HTTP jobs every 2s and sends DB-backed heartbeat every 60s; primary Neon compute 0.25CU fixed; default suspend policy 5min idle. Item3 and item6 were deployed: Vercel removed request/cold-start DDL and switched /health to read-only; GitHub monitor has deep verification every 12h and metadata-only 30min. C8 Hostinger listener is not yet in production.

## FAILED_AVOIDED
Do not manually suspend production compute, change timeouts, delete queues, OAuth records, or disable lease recovery to manufacture a billing reduction. Do not confuse lower SQL counts with billable savings or compare non-equivalent load windows as causal proof. No new infrastructure or costs; do not request human action before checking authorized routes.

## SUCCESS_SIGNAL
A dated before-and-after consumption rate adjusted for period length and compute size, live auto-suspend evidence after genuine idle >5min, preserved protected auth, single C8 SYSTEM with independent Git queues, idempotency and no uncertain jobs. Counter deltas may support but cannot substitute billing evidence.

## FAILURE_SIGNAL
Project still ACTIVE with no scale-to-zero, CU-hours still accumulating near 0.25CU per hour, SQL wake paths persist, telemetry baseline lacks exact times, or broker/C8 deployment not accepted.

## TEST_VALIDITY
Read-only project/endpoint telemetry and PG counters; Neon free plan lacks hourly consumption_history API, so avoid fabricating a precise hourly spend history. Respect app metric refresh delay and other active agents; report a negative/partial result if actual savings cannot be established.
