# Kwai direct SEND rerun invalidated by android-emulator-runner per-line shell semantics
STATUS: PARTIAL
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37391449031
JOB: 112037257575
COMMIT: a1cbe6dc67ad876652f147529612f92c0608dbf3
SUPERSEDES: test-hub/findings/20261005-2109-kwai-direct-send-runtime-retry-running.md

BASELINE_PROVEN: Manifest ACTION_SEND contract and FSM MAIN remain unchanged.
FAILED_AVOIDED: no inference about media ingress is taken from workflow failure; no Publish action occurred.
SUCCESS_SIGNAL: not reached.
FAILURE_SIGNAL: not reached.
TEST_VALIDITY: INVALID/NOT_TESTED. The action wrapper invoked the configured multiline script as separate `/usr/bin/sh -c` commands. The log shows `/usr/bin/sh -c bash <<'BASH'` followed by a separate `/usr/bin/sh -c set -euo pipefail`, which failed before `kwai_vault_install.sh`, FSM, media generation or ACTION_SEND.

## Resultado
The first shell repair still depended on multiline shell semantics that this action does not preserve. The decisive log proves each script line is executed independently by `/usr/bin/sh`; the heredoc opener cannot change the shell used for subsequent lines.

## Consequência
Stop changing shell syntax inside the YAML multiline block. Move the entire experiment body into a repository shell script with `#!/usr/bin/env bash`, and configure android-emulator-runner with exactly one command: `bash kwai_direct_send_runner.sh`. This is the next causal harness change; the media-route hypothesis remains untested.
