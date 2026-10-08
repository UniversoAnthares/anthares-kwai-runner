# Asaas webhook fail-closed repair lease
STATUS: RUNNING
AREA: wordpress-payments
DATE: 2026-10-08
RUN: none
JOB: none
COMMIT: 85aa1ed09076ba18bc880f397fe3e8a01afe9e09
SUPERSEDES: none

BASELINE_PROVEN: current WordPress GitLab PHP QA success, existing Asaas webhook bearer token verification.
FAILED_AVOIDED: no production webhook regeneration, no real financial operations, no direct main overwrite, no token logging.
SUCCESS_SIGNAL: isolated branch patch fails closed on corrupt/unpersisted token and does not delete existing provider webhook before successful replacement; hosted PHP lint and deterministic regression evidence.
FAILURE_SIGNAL: PHP lint error, unguarded deletion or uncontrolled token rotation.
TEST_VALIDITY: review complete source before patch; test on isolated branch; never claim live acceptance.
Lease duration: 30 minutes from creation. Scope: anthares-pix-sales/includes/67-asaas-recebimentos.php only.