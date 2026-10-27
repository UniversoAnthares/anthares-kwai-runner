# Lease — CORTES-QUOTA-01 cross-provider cancellation and Neon QA
STATUS: PROVEN
AREA: architecture / quota-cancel-failover
DATE: 2026-10-27
RUN: https://github.com/UniversoAnthares/anthares-clipper/actions/runs/40496796163
JOB: 122164286587
COMMIT: 3bdcb00698356eb0882cf0a42a5592432c3ba59c
SUPERSEDES: none

## Owner and scope
ChatGPT-owned append-only documentation of CORTES quota controller tests and Neon QA schema only. The code paths were implemented in Anthares Clipper PR #211/#212 and merged to main. No leases or ownership claimed over productive runtime, social accounts, credentials, publication states, or existing QA branches.

## Coordination
Do not change or cancel shared workflows while documenting. Any further schema deployment must re-read the live branch and reconcile the pre-existing incompatible QA outbox layout before touching its table.
