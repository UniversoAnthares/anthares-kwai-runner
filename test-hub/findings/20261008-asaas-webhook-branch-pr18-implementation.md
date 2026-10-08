# Asaas webhook token safety repair on isolated branch
STATUS: PARTIAL
AREA: wordpress-payments
DATE: 2026-10-08
RUN: https://gitlab.com/UniversoAnthares/anthares-wordpress/-/pipelines/2927070498
JOB: pending
COMMIT: 42b5d490d8c9af09fa855a8a7bb1d8e3c36d72ce
SUPERSEDES: 20261008-lease-asaas-webhook-failclosed-repair.md

## Change
GitHub PR https://github.com/UniversoAnthares/anthares-wordpress/pull/18, branch fix/asaas-webhook-failclosed-20261008, mirrored to GitLab branch same SHA. Target only anthares-pix-sales/includes/67-asaas-recebimentos.php. Existing stored token that cannot decrypt now fails closed instead of silently rotating. New token generation requires encryption, successful update_option, exact persisted read-back and decrypted token comparison before returning. Webhook registration aborts on empty token. Existing webhook with same URL is preserved instead of deleted before creating a replacement. Git diff --check passed. Hosted GitLab PHP QA pipeline 2927070498 was RUNNING at last check; do not mark PHP QA PROVEN until actual job log confirms.

## Safety boundaries
No production deployment, no live token change, no Asaas financial operation, no main branch modification. Isolated functional tests of failed encryption/DB storage and webhook discovery remain necessary. Do not merge automatically while provider webhook token equivalence and backward compatibility have not been assessed.
