#!/usr/bin/env bash
set -Eeuo pipefail
P=${CI_PROVIDER:-unknown}
echo PROVIDER=$P
echo TEST_VALIDITY=PROVIDER_SHELL_READY

if [ "${ANTHARES_BROWSER_QA_ENABLED:-0}" = "1" ]; then
  ANTHARES_BROWSER_QA_CASES=${ANTHARES_BROWSER_QA_CASES:-40} \
    bash ci/shared/anthares-browser-runtime-qa.sh
fi

echo SUCCESS_SIGNAL=PROVIDER_HUB_OK
