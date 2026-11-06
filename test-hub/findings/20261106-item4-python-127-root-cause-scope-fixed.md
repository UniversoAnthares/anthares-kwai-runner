# AOI item 4 — Python interpreter failure root cause corrected in source
STATUS: PARTIAL
AREA: architecture/forgejo-main-ci-cd
DATE_UTC: 2026-11-06T00:33:28.109Z
OWNER: chatgpt-aoi4-hostinger-py-20261106
SUPERSEDES: 20261106-lease-aoi4-hostinger-python-selection.md
LEASE: CLOSED
RUN: https://anthares.us/forgejo/anthares-admin/anthares-kwai-runner/actions/runs/1
COMMIT_SOURCE: 9eb723d9415c40c1e907d706763217072a18408c
BASE_HEAD: ba6ffe983a2112014db7926cf0bd6c39a1ea6061
GOVERNANCE: manifest version 223433740e807a90

## Actual failed attempt and cause
Persisted Forgejo job log, public read GET /actions/runs/1/jobs/0/attempt/1/logs HTTP 200, timestamp 2026-11-05T16:11:14Z:
- runner v13.2.0 task 473; checkout SHA 2cba98456578cf2164bfc519e10f52a374f4894e PASSED.
- ANTHARES_FORGEJO_MAIN_IDENTITY=PASS.
- workflow script 2.sh line 4: python3.11: command not found.
- runner exit 127, CI FAILED, CD SKIPPED; no private CD receipt.

## Scoped code change
.forgejo/workflows/anthares-main-ci-cd.yml: both CI and CD now look for already installed CloudLinux Python 3.11/3.12/3.10 and Python on PATH, verify version >=3.10 and sqlite3, and reuse selected interpreter for actual py_compile, unittest and private receipt.
Missing interpreter fails explicitly with ANTHARES_FORGEJO_PYTHON310_UNAVAILABLE, without installing anything, skipping tests, or claiming PASS.
No GitHub/Forgejo security admin operation, runner registration, publication or media changed.
Locally executed exact selection snippet: bash -n PASS and version selection Python 3.13.5 PASS.
Hostinger Python presence remains UNVERIFIED; local check is not a Forgejo production test.
Mirror sync, manual authorized dispatch, terminal job proofs and private receipt remain required to declare DONE.
FAILED_AVOIDED: no repeat of unchanged run #1, paid Python installation, personal PC executor or denied Forgejo admin action.
COST: no new paid service. ROLLBACK: revert source PR.
