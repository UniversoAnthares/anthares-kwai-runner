# Kwai: reconhecer ACK local obsoleto mediante leitura autenticada do Neon
STATUS: RUNNING
AREA: kwai
DATE: 2026-11-13
RUN: none
JOB: none
COMMIT: 73db211c84788da26db4593f6dbfc8c767691ef5
SUPERSEDES: none
OWNER: ChatGPT / Anthares Kwai
SCOPE: signed kwai-job-terminal-read (read-only), cortes_neon_queue_client.py, kwai_physical_queue_daemon.py, existing offline regression.

## BASELINE_PROVEN
Neon cortesequeue production 76, SQL at 2026-11-13 18:37 MS: 3 local ACK jobs confirmed, 1 cancelled, exact lease generations retained, 0 started/uncertain. Local Android logs repeatedly attempt unsupported reconcile operation; account secondary holds published_pending_ack for already-confirmed server job and blocks next lease. Existing credential is the RSA physical-device signature. No legitimate new post needs to be attempted.

## FAILED_AVOIDED
Never requeue, alter SQL, call legacy reconcile, submit a Kwai post or Android UI in QA; do not use GH Android or modify Windows files. Strict author/target/gen/role check, server proof and WordPress completed for confirmed, exact discarded proof for cancelled. Do not let empty or ambiguous results unlock. Oracle/CutMotions/cost>0 are excluded.

## SUCCESS_SIGNAL
Offline tests prove 4 observed terminal states recognized with canonical generation and author; reject mismatched owner, generation, proof, URL, absent ID, pending/uncertain/leased, forged credentials, and cross-account. Existing CI passes. No media publishing or database mutating calls.

## FAILURE_SIGNAL
Any local ACK cleared before terminal proof, false positive on uncertain or mismatched generation, exposed unauthenticated lookup or queue mutation, CI failed.

## TEST_VALIDITY
CI-only static/AST checks; Neon live SELECT performed earlier and used strictly as source of expected cases. Deploy and Windows process replacement require later controlled independent review.
