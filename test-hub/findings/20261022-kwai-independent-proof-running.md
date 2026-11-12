# Kwai proof incident: cross-device public link and media identity
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-22
RUN: none
JOB: none
COMMIT: 1db074842917a70288987c65ed8501864123be74
SUPERSEDES: none
LEASE_AREA: kwai-publish
LEASE_OWNER: ChatGPT 2026-10-22 22:44 America/Campo_Grande
LEASE_MAX_EXPIRY_UTC: 2026-10-23T03:15:00Z

## BASELINE_PROVEN
Kwai daemon was paused after wrong-link incident. Positive independent verification of k.kwai.com/p/WCAQrpD2 and /p/kDaNBC9y passed; cross-title negative verification rejected. Neon has 48 queued jobs. A physical Android publication is ongoing through a fenced lease. Production local publisher patch is backed up in .state incident directory.

## FAILED_AVOIDED
No clipboard synchronization with Windows. Do not recognize a mere profile image or post timestamp as final proof. Do not requeue UNCERTAIN jobs, reset shared main, or interrupt in-flight publications.

## SUCCESS_SIGNAL
Static tests for independent Kwai deep-link title and author proof + strict binding to job/media SHA, correct end-to-end proof recovery, production post URL and Neon confirmation.

## FAILURE_SIGNAL
Any contradictory post title/account, unverified URL, missing link, stale file SHA, missing proof, or runtime unavailability fails closed.

## TEST_VALIDITY
Synthetic tests never publish. A real post is proven only by independent Kwai URL verification and a fenced Neon completion.
