# Kwai publish workflow mutation corruption caught before publication
STATUS: FAILED
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37387467335
JOB: workflow parser/harness
COMMIT: 071c53eaf94eca0aaf6a055503c26c932656ec24
SUPERSEDES: none

BASELINE_PROVEN: test-hub/findings/20261005-2320-lease-kwai-publish-hardening.md
FAILED_AVOIDED: no real publication was attempted; schedule had already been removed.
SUCCESS_SIGNAL: n/a
FAILURE_SIGNAL: workflow structure corrupted around Confirm central queue publication.
TEST_VALIDITY: this is a harness/configuration failure, not evidence about Kwai publication.

## Resultado
A text replacement used while hardening the workflow duplicated/truncated YAML around the confirmation step. GitHub created run 37387467335 and it failed before useful publication execution. Inspection of HEAD exposed the malformed block. The workflow was then rebuilt atomically in commit 9dec9833c497f9b801af93974f7ccb3f32171cc3.

## Consequência
Do not reuse commit 071c53e. Validate the rebuilt workflow statically before any trigger. No real publish conclusion may be inferred from this run.
