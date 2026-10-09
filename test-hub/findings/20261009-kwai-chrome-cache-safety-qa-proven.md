# Chrome session encrypted-only cache security QA
STATUS: PROVEN
AREA: kwai-chrome-cache-safety
DATE: 2026-10-09
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37936417696
JOB: 113839485691
COMMIT: e60ef38852953ebfb87730abe632920f0cc8dd17
SUPERSEDES: none
LEASE_CLOSED: test-hub/findings/20261009-kwai-chrome-cache-safety-lease-1791551890.md

## Objective
Prevent decrypted Chrome browser cookies/tokens from being written to disk or saved in Actions cache, and keep unauthenticated probes fail-closed. No Android emulator, no PC, no credentials.

## Result
PROVEN for isolated synthetic and source-regression scope: 8/8 tests passed on GitHub-hosted Ubuntu. The Chrome session code now decrypts into memory and encrypts in memory, removes legacy plaintext storage-state, caches only .kwai-session-cache/kwai-session.enc, and uses isolated kwai-encrypted-session-v2 cache keys to prevent restoration of older plaintext-capable archives. OAuth popup URLs are logged without query parameters. Browser popup/method waits are bounded.

## Decisive evidence
Run 37936417696 job 113839485691: 'Ran 8 tests in 0.215s' followed by 'OK'. Independent synthetic cross-run proof 37935784822: CRYPTO_PROOF_CREATE encrypted=true synthetic=true; CRYPTO_PROOF_VERIFY restored=true tamper_rejected=true synthetic=true. Session-key presence previously verified by run 37933084293.

## Limits and consequences
Real Kwai authentication is NOT proven: no authenticated Chrome storage state or account-identity evidence exists. Never infer login from a missing login button. The live Chrome probe 37935956989 was still running when this finding was recorded and is NOT counted as a success. Do not touch the concurrently running kwai-login agent, Android workflows, or its lease. Preserve encrypted-only cache namespace and fail-closed identity checks.
