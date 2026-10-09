# Kwai cached Android fastpath to actual application launch
STATUS: RUNNING
AREA: kwai-speed
DATE: 2026-10-09
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37940202375
COMMIT: 2ef64cbc80ac3fc1728f61c60380f5275fc3c9ea
SUPERSEDES: none

## Objective
Close redundant Android startup benchmarking and integrate the already-PROVEN parallel v5 snapshot restore into an independent Kwai install/foreground acceptance path. This is an isolated app-launch probe, not a login/publish test.

## BASELINE_PROVEN
test-hub/findings/20261009-kwai-speed-parallel-v5-proven.md: full AVD slim v4, Android system image v1, headless emulator v2 parallel restore; explicit kwai-ready load, 6s boot, 40s total in proven hosted runner. Previous strict v2 archived snapshot also PROVEN; preserve historical records.

## FAILED_AVOIDED
Do not repeat bare login-router, authorization intents, pre-MAIN blind automation, snapshot-only incomplete state, or failed cache path version mismatch. No login-agent files or state altered.

## SUCCESS_SIGNAL
Cache hits all three; V5_ACTUAL_LOAD=true and V5_RESULT=PROVEN_SUB10; vault SHA256 validated; adb install-multiple succeeds, package com.kwai.video exists, launcher invocation succeeds, foreground activity belongs to com.kwai.video. No authenticated identity inferred.

## FAILURE_SIGNAL
Any missing cache, snapshot fallback, failed APK install, missing package, or foreground activity not Kwai.

## TEST_VALIDITY
Fresh GitHub-hosted runner, isolated workflow. Failure to download vault or runner infrastructure fault invalidates app hypothesis, not proof of Kwai incompatibility. No local PC.

## SESSION BOUNDARY
Authentication persistence remains UNPROVEN here. Session/login mutation requires the separate kwai-login lease holder; never store tokens, cookies or passwords in findings. Existing kwai-chrome-session isolated crypto lease is a different synthetic-only path.

## Run status
Queued when recorded. A follow-up append-only finding must record decisive logs and actual outcome.
