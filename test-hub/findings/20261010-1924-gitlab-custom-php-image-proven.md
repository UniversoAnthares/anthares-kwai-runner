# GitLab Render custom executor supports actual PHP 8.5 image
STATUS: PROVEN
AREA: gitlab-qa
DATE: 2026-10-10
RUN: https://gitlab.com/UniversoAnthares/anthares-wordpress/-/jobs/17085304601
JOB: 17085304601
COMMIT: 77b910ac108c3feffed0821add5d9b7e519c04b2
SUPERSEDES: test-hub/findings/20261010-1921-lease-gitlab-custom-image-isolated.md

## Evidence
- Isolated retry of canceled job 17084427523 created job 17085304601 on runner `anthares-render-qa` with tag `render-qa`.
- Custom executor checked out protected QA branch commit 77b910ac.
- udocker exported `php:8.5-cli`; job ran actual `PHP 8.5.11 (cli)` and emitted `ANTHARES_CUSTOM_IMAGE=PROVEN`.
- Job status `success`, finished 19:23:39Z; no local PC or paid runner.
- Six other jobs on the pipeline remain `ci_quota_exceeded` because their `tags: []` require GitLab-hosted runners; this is independent of image compatibility.

## Consequence
Do not rerun the proven PHP image probe. To close MR !34, change the draft branch CI config to avoid shared-runner tags and preserve original images/artifacts; test each remaining image on custom runner. GitLab connector file update was blocked by tool security settings. Keep MR draft until all required jobs succeed. No main/production merge.
