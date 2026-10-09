# Codespaces bridge pagination bug fixed in repository; live activation pending
STATUS: PARTIAL
AREA: kwai-login
DATE: 2026-10-09
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37965285297
JOB: none
COMMIT: 4c4c59d689435d629379b10e47147a1fdf8d27a1
SUPERSEDES: 20261009-lease-kwai-bridge-pagination-recovery.md

## Objetivo
Restore autonomous issue #12 control after the command channel exceeded one GitHub comments page, while preserving the live Chrome profile.

## Resultado
Root cause proven: issue #12 page=2 contains new bridge commands, while bridge v1 polls only comments?per_page=100. Added kwai-command-bridge-v2.py polling newest comments first, added owner_probe requiring exact @universo.anthares route + owner-only Edit profile + no login gate, and changed kwai-start.sh to restart only the bridge into v2 while leaving Chrome/profile untouched. Security QA run 37965285297 completed SUCCESS.

## Evidência decisiva
GitHub REST page=2 contains post-boundary commands including finalIdentityRefresh20261009a. The old live bridge produced no response because it cannot see page 2. Repository QA for commit 4c4c59d passed.

## Consequência
Do not post more commands expecting bridge v1 to see them. Activate current checkout once with `git pull --ff-only && bash .devcontainer/kwai-start.sh`; after that v2 can see newest commands regardless of the 100-comment boundary. Then run owner_probe, and only if identity_verified=true combine it with operational_create_surface=true before any upload/publication. Chrome must not be rebuilt or logged out.
