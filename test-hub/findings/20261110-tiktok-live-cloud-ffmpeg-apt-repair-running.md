# TikTok LIVE cloud — reparar ausência de FFmpeg no runner Ubuntu
STATUS: RUNNING
AREA: tiktok-live-cloud-preflight
DATE: 2026-11-10
OWNER: chatgpt-tiktok-live-20261110
LEASE_AREA: tiktok-live-cloud-preflight
LEASE_EXPIRES: 2026-11-10T18:00:00Z
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/42845339213
JOB: 129931275299
COMMIT: a29302036fa3f4809bb91d0d10460b331e7ea5d0
SUPERSEDES: none
BASELINE_PROVEN: push workflow launched in GitHub Ubuntu; checkout passed, preflight step returned ANTHARES_TIKTOK_STATUS=ffmpeg_not_installed, dry-encode skipped; no TikTok ingest attempted.
FAILED_AVOIDED: no new account session, TikTok RTMP key, live room or user-device workload; no Kwai changes.
SUCCESS_SIGNAL: newer clean workflow run prints ANTHARES_HLS_PREFLIGHT_OK=1 and ANTHARES_DRY_ENCODE_OK=1; all steps green; no TikTok transmit.
FAILURE_SIGNAL: absence of required markers, apt setup failure, ffmpeg input failure or job failure; do not classify LIVE as proven.
TEST_VALIDITY: same workflow on isolated feature branch, Ubuntu hosted FFmpeg newly installed and 8-second null-output media encoding, not a production broadcast.
