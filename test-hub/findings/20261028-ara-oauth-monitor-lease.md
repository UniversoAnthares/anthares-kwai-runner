# ARA item 6 — OAuth DDL and controller monitor hot path
STATUS: RUNNING
AREA: anthares-remote / neon-idle-optimization / oauth-monitor
DATE: 2026-10-28
OWNER: ChatGPT GPT-6 (fixed item 6)
RUN: none
JOB: none
COMMIT: 780290e39bf6dc56ee1af7503b37da9a5e219074
SUPERSEDES: none

## BASELINE_PROVEN
Production Vercel anthares-remote-primary READY dpl_34YfhFrAn84AxPvgW3XRrrhu6EJd at exactly 780290e39bf6dc56ee1af7503b37da9a5e219074, primary router.mjs blob 17d4ffdef1af87ac7310c0f20aecbc26eb5d99c0, GitLab peer different older blob cd59e393d76068df4ad3236da4aec1fa716c741e. Neon production ara_oauth_consumed exists and UNIQUE PRIMARY KEY (kind,issuer,jti) enforces replay; 61580+ signed records, expired records remain; no destructive SQL authorized. Current /health uses status() causing 4 UPDATEs and 2 SELECTs plus SELECT 1; both OAuth consume paths call CREATE TABLE/INDEX in cold-start ensureSchema. C8 SYSTEM heartbeat 60s and idle polling 2s, liveness 30s, OAuth guard every ~5min, GitHub continuity monitor every 10min; C8 wake item5 not live. Local presence TTL 90s must remain.

## FAILED_AVOIDED
Do not change the OAuth token signing/replay uniqueness, leased jobs, SAFE_RETRY, idempotency or wake notifier; no DB/schema destructive statement. Do not weaken device connected TTL, authentication failures, independent supervisor/failover. Do not modify reserve Vercel while another team operates it. No new PC artifacts, processes or services, no extra costs, no merge onto concurrently changing main.

## SUCCESS_SIGNAL
Exact readback without DDL in OAuth runtime, still INSERT ON CONFLICT for signed replay, no status() side-effect in public health; READY production, /health correct and ARA status/command through same controller. Baseline network probing preserved, no user secrets published. OAuth metadata and unauthorized route behavior pass.

## FAILURE_SIGNAL
Schema absent, CI build fail, health 503 or device disconnected while agent is alive, failed OAuth auth, replay bypass, alternate production deploy drift.

## TEST_VALIDITY
Static source and READY are not acceptance without live health, authenticated status and replay invariant. Heartbeat remains on Neon until external presence path item5 is safely proved; this limitation must not be called full CU-h savings. Lease scoped to isolated branch, max 30 minutes; close with append-only finding.
