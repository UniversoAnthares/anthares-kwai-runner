# Lease — CORTES-ISO-06 TikTok diagnostic environment
STATUS: RUNNING
AREA: tiktok-session
DATE: 2026-10-25
RUN: none
JOB: frente-a-iso06-discovery-20261025T1215Z
COMMIT: 05ae946b79949cb6d43e4134972c10943c9b62a1
SUPERSEDES: none
EXPIRES_UTC: 2026-10-25T12:50:00Z

## Objective

Create a dedicated GitHub Actions environment for the non-publishing TikTok environment matrix and bind only that matrix job to it. No workflow dispatch, secret creation, session read, publication, or deployment is permitted by this lease.

## Baseline and avoided failures

The matrix workflow has no environment binding. GitHub inventory lists no dedicated TikTok environment. The 30-environment matrix may retrieve an existing central session, so it must not be dispatched as a configuration probe. Existing publishers and environments are out of scope.

## Signals

- SUCCESS_SIGNAL: protected environment exists and proposed job binding is on a draft branch; YAML parses without execution.
- FAILURE_SIGNAL: API refusal, stale base, or any change outside the environment and workflow declaration.
- TEST_VALIDITY: no GitHub Actions run is created and no session/cookie material is accessed.

## Fencing

Only codex-delegated-frente-a may mutate this ISO-06 lease before expiry. Abort on concurrent change, missing optimistic SHA, or unrelated dirty-file overlap.
