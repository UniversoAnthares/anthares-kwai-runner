# CORTES WP QA SYSTEM identity — source and actual authorized SSH read PROVEN
STATUS: PROVEN
AREA: wordpress-qa-auth
DATE: 2026-10-27
BRANCH: fix/wp-qa-system-ssh-authorization-20261027
SUPERSEDES: 20261027-lease-wp-qa-system-task-ssh-chatgpt.md
GITHUB_PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/1720

## Observed failure
Live scheduled task Anthares CORTES P0 QA Immediate Independent ran under NT AUTHORITY\\SYSTEM as S-1-5-18 and returned result 2; through 2026-10-27 19:18 local it recorded `source=wordpress code=AUTH_MISSING`, despite the independent GitHub runner's own SSH success. Source used only the GitHub-runner RUNNER_NAME environment identity for SSH fallback.

## Causal repair
Retain existing exact runner. For the pre-existing host DESKTOP-FTDK0HP only, allow the actual Windows process SID S-1-5-18 returned by whoami /user; other hosts and principals fail closed. Existing SSH alias, StrictHostKeyChecking=yes, read-only WP-CLI, and no-fallback-on-REST-401/403 remain unchanged. No new secrets, login, production write, job dispatch or public posting.

## Evidence
- Anthares Remote read-only task/identity verification: SYSTEM, scheduled task `Principal.UserId=SISTEMA`, exact machine, SSH alias and key already present.
- Real authenticated read-only WP-CLI probe as SYSTEM returned exit code 0.
- SHA-pinned code 00f214570b078f83ed5dc32012a39150be81c0e1 executed *in memory* under real SYSTEM without writing files. Result `QA_SID_CHECK=True`, `CORTES_WP_QA_AUTH_SOURCE=HOSTING_SSH_READONLY`, `QA_WP_SSH_ITEMS=True`, `EXIT_CODE=0`; ARA job 72ff6276b6809fa96e8b221c74011c30.
- All 28 isolated Python regression tests passed with zero failure and zero error on that immutable commit. ARA job 73f02f7cc9623902661ba32bddd29194. No network publishing effects in tests.

## Follow-up acceptance gate
The scheduled Windows task pulls its canonical source from Codeberg before GitHub. Integration and mirror propagation must be checked independently; source-level real SSH success does not assert the scheduled task is already repaired. A fresh `source=wordpress` scan without AUTH_MISSING and terminal task exit 0 will close that deployment acceptance separately.
