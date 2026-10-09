# Kwai login exit 2 exact source cause — read-only handoff
STATUS: PROVEN
AREA: kwai-login
DATE: 2026-10-09
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37940330000
JOB: 113852768706
SUPERSEDES: none

## Decisive runtime evidence
Runs 37940330000 (job 113852768706) and 37940318452 (job 113852728836) reached KWAI_LOGIN_UI_OPENED and KWAI_OWNER_INTERACTION_READY, then failed with '/tmp/kwai_remote_android_login.runtime.sh: line 366: unexpected EOF while looking for matching single quote' and exit code 2.

## Source root cause (read-only)
At repository HEAD, kwai_remote_android_login.sh line 362 contains a truncated conditional: if tap_label '^(I agree|Concordo)
The closing quote, regex suffix, command terminator and enclosing conditional are missing. At end of the source, a second detached duplicate of the Google SSO block begins after 'log "FAIL: login-window-expired-2700s"; exit 28' with '; then', demonstrating corrupted duplicated text. kwai_remote_android_login_with_restore.sh copies the source into /tmp/kwai_remote_android_login.runtime.sh and patches other sections but does not repair this broken source section. The Bash syntax error is therefore deterministic and unrelated to credential rejection or Android startup.

## Required fix for authorized kwai-login owner
Repair the original Google agreement tap_label condition and close its if/fi structure, remove the detached duplicate block after the final exit, and require bash -n on the source and generated runtime script BEFORE launching Android or opening the remote owner interaction. Add a fail-closed syntax preflight to prevent further wasted 4-6 minute runs. Recheck syntax before invoking a login workflow. No secrets or account credentials should be logged.

## Constraints
Only read-only source/log analysis performed; no login-agent file modifications, no competing login lease, no local PC. This finding is a coordination handoff, not evidence of authenticated session.
