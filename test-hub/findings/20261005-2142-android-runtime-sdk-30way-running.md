# Android runtime SDK harness 30-way discovery
STATUS: RUNNING
AREA: kwai
DATE: 2026-10-05
RUN: pending
JOB: 30-way Android SDK/emulator harness discovery
COMMIT: pending
SUPERSEDES: test-hub/findings/20261005-2135-lease-kwai-login-agent-runtime.md

BASELINE_PROVEN: Agent build PROVEN; Kwai vault checksum/download PROVEN in failed runtime run 37397864424.
FAILED_AVOIDED: run 37397864424 stopped before emulator because sdkmanager was not on PATH. No Agent/Kwai runtime conclusion is reused or repeated.
SUCCESS_SIGNAL: one or more variants proves a concrete command/path/install strategy that can resolve sdkmanager/emulator tooling on ubuntu-24.04 and reports SDK_STRATEGY_PROVEN.
FAILURE_SIGNAL: a variant's distinct SDK discovery/install strategy cannot expose a usable sdkmanager path.
TEST_VALIDITY: each matrix job first proves checkout + Java + shell environment; no Kwai/Agent runtime hypothesis is tested in this matrix. Results are harness evidence only.

## Matrix
30 independent SDK-toolchain discovery variants are run concurrently after the same harness precondition. This matrix exists only to close the sdkmanager PATH/toolchain cause quickly; successful strategy will be folded back into one runtime validation.
