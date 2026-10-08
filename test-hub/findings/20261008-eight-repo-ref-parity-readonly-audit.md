# Eight-repository GitHub/GitLab remote ref audit
STATUS: PARTIAL
AREA: provider-redundancy
DATE: 2026-10-08
RUN: none
JOB: read-only git ls-remote
COMMIT: none
SUPERSEDES: none

Read-only `git ls-remote` checks of main on GitHub and GitLab showed identical commit SHA for anthares-wordpress (85aa1ed0) and github-slideshow (007a96d5). Different commit SHAs for anthares-clipper (GH eca63a28, GL 2dbaf2e5), anthares-kwai-runner (GH f60e4300, GL aabce8b8 at probe time), anthares-transcricao (GH c30a03c6, GL 91ca7196), anthares-telegram-relay (GH e2f986d1, GL a0f21db1), wiki (GH e70abc9e, GL 4d7bf759), home (GH df291d20, GL 0ef87380). Different commit SHAs do not prove different trees. Subsequent safe fast-forward brought kwai-runner GitLab main to GH f60e43002dbf375f4041638e648fd7d135359c01. Other repos intentionally NOT mirrored: tree equality and divergence have not been freshly proven. No force pushes. Recommend inspect tree IDs and ancestry before any other provider reconciliation.
