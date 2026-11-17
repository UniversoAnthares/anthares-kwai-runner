# Studio G4 — escrita funcional restrita ao piloto privado
STATUS: RUNNING
AREA: anthares-studio/g4/private-admin-write
DATE: 2026-11-17
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-g4-private-admin-write-20261117
SOURCE: UniversoAnthares/anthares-wordpress PR #315 HEAD 2e2935f9cd8f6d95cb9d64a79ca871d93267736b
PEER: GitLab branch fix/studio-g5-acf-dual-approval-20261117 absent (404).
POLICY_SHA256: CA1F14B74908C9E6EB3E6D225572EBF217583F76837DD45611470C5432A09138
SCOPE: a plugin anst_permission() server permission change plus regression test in existing Studio files, isolated branch and draft PR; no changes in /estudio or live data.
BASELINE: G4 readonly parity on live DB confirmed 71 AEST and 71 ANST including 31 trashed each, 7 Delta SHA matches, 0 source mismatches, REST GET count parity for 2 owners; 28 vs 28 routes. A real account /studio reported 423 on creating project; anst_writes_enabled=0.
PLAN: when write flag becomes enabled in a controlled pilot, default restriction to manage_options users, with non-admin POST/DELETE returning 403; GET remains unchanged. Writes flag still defaults OFF.
BLOCK: no changes to production options, AEST data, plugin original, commercial entitlements, public visibility, hooks for other plugins, or browser controls in this code PR. Production activation requires backup+restore proof, visual G4, controlled tests.
ROLLBACK: revert isolated PR changes. The branch is not authorized for auto-merge or auto-deploy.
