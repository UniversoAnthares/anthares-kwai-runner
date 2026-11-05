# AOI #13 — correction of WordPress source SHA, 2026-11-05
STATUS: PROVEN
SUPERSEDES: 20261105-aoi13-7-of-8-gitlab-source-backups-proven-leases-closed.md (WordPress source SHA field only)
SOURCE_RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/42009258489
JOB: 127183785067
CORRECTION: the source ref was moving as a concurrent GitHub update landed. The real accepted mirror receipt (job log) states WordPress GitHub main at `910ca5982d93affcfd6070f84810f73915ab5041`, not the earlier read-only snapshot `e89aee9f53b42199bc9cf9691fa5b259b79edb0d`.
DEST_GITLAB_MAIN: `9ea3e3b641229cb69988c3c8233dd69284429335`
SOURCE_TREE: `c239c2d4dc4519b6e0ab698f1344801a4572fd28`
DEST_TREE: `c239c2d4dc4519b6e0ab698f1344801a4572fd28`
RESULT: MERGED_PRESERVING_BOTH; independent blob comparison after the run 740/740, additional 0. Existing records and leases remain otherwise valid. No new execution was launched for the correction.
