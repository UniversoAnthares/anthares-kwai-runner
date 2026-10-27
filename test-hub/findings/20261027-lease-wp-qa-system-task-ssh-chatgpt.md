# WP QA P0 SYSTEM scheduled-task read-only SSH authorization
STATUS: RUNNING
AREA: wordpress-qa-auth
DATE: 2026-10-27
OWNER: ChatGPT GitHub connector
BRANCH: fix/wp-qa-system-ssh-authorization-20261027
LEASE: 30 minutes from creation
RUN: none
SUPERSEDES: none

BASELINE_PROVEN: 20261027-wp-qa-authenticated-ssh-fallback-proven.md establishes the approved named Actions runner SSH route; the Windows SYSTEM scheduled task logs AUTH_MISSING every five minutes. Read-only ARA inspection verified the scheduled-task principal SYSTEM on DESKTOP-FTDK0HP, strict-host-key SSH configuration, existing identity file and successful wp option get siteurl via authenticated remote WP-CLI (exit 0).
FAILED_AVOIDED: Never forge RUNNER_NAME or disable identity checks; never substitute on explicit REST 401/403. No new credential, production write, publisher dispatch, or desktop interaction.
SUCCESS_SIGNAL: The SYSTEM identity is recognized only by verified Windows SID S-1-5-18 and exact authorized hostname, named Actions runner remains eligible, other identities rejected, original SSH read-only route and strict host-key checks preserved; observed independent Windows QA scheduled result after GitHub+Codeberg source propagation.
FAILURE_SIGNAL: Any unintended principal allowed, SSH/WordPress read failure, source divergence, or concurrent lease.
TEST_VALIDITY: Syntax and focused unit regression plus real SYSTEM read-only WP-CLI check only; a green job absent WordPress-source PASS is insufficient.
