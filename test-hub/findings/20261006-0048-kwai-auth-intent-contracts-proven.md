# Exact exported Kwai auth intent contracts proven
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37388775209
JOB: 112028590293
COMMIT: b2e6551285ab6ad2d81aef4b399e7b1b141beb4d
SUPERSEDES: test-hub/findings/20261006-0040-lease-kwai-auth-intent-details.md

BASELINE_PROVEN: test-hub/findings/20261006-0038-exported-kwai-auth-entrypoints-proven.md
SUCCESS_SIGNAL: exact action/category/scheme/host metadata recovered.
FAILURE_SIGNAL: no usable intent-filter data.
TEST_VALIDITY: aapt Manifest extraction completed with TEST_VALIDITY=OK.

## Resultado
OpenAuthActivity accepts VIEW + DEFAULT + BROWSABLE with scheme com.kwai.video. LivePartnerAuthActivity accepts VIEW + DEFAULT + BROWSABLE with ikwaipartner://auth. KwaiAuthActivity accepts VIEW + DEFAULT + BROWSABLE with ikwai://authorization, kwai://authorization and ikwaibulldog://authorization.

## Consequência
Runtime probe may now invoke exact Manifest contracts. Prefer ikwai://authorization and kwai://authorization as the most directly auth-named routes; observe foreground/UI and whether internal LoginActivity appears. Do not supply guessed credentials or query parameters.
