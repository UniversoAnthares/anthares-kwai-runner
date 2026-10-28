# AOI — item fixo 6: preservação dos cinco repositórios privados essenciais
STATUS: PROVEN
AREA: architecture/forgejo-private-git-migration
DATE: 2026-10-28
RUN: evidence retained in authorized private Hostinger Git mirror recovery receipts; prior independent readback 2026-10-28 20:14 UTC
JOB: existing Hostinger mirroring service; no new job launched in this finding
COMMIT: GitHub PR #1752, #1800; current GitHub HEAD validation on 2026-10-28
SUPERSEDES: only the **item 6 status classification** of 20261028-forgejo-mirror-cdn-readback-verified.md; its GitLab divergence/CI conclusions remain unchanged.
LEASE: ENCERRADO — this entry is documentary, no mirror/publisher write.

## Acceptance and provenance
BASELINE_PROVEN: the immutable item 6 requires a named inventory, repository privacy, preserved Git refs and recoverable objects, distinct from item 13 (independent GitLab historical refs), item 7 (continuous synchronization) and publishing/CI admission.
SUCCESS_SIGNAL: existing Hostinger verification of the five private allowlisted GitHub→Forgejo repositories completed with 5/5 exact branch-ref sets, 0 differences, private destination status and clean Git connectivity/fsck. The earlier recovery drill covers 13/13 nonempty GitHub sources, and 2 legitimate empty sources are a separate fixed item.
TEST_VALIDITY: real Git refs comparison and repository-level fsck, not mock or just workflow green; previous operator evidence recorded 2026-10-28 20:14 UTC, using the existing Hostinger mirror and no new provider/cost.
SOURCE_READBACK: on 2026-10-28 the authenticated GitHub API reverified **five private repos**, all with canonical `main`, original migration inventory intact. A source branch added later to one repo changes the ongoing sync state, tracked by item 7; its current main was independently matched by a later real Forgejo CI run.
FAILURE_SIGNAL: a future source/target ref mismatch or inability to restore requires an item 7 drift incident and a new independent readback, not reinterpretation of the five-repository migration. No current live Forgejo ref fetch was obtained in this audit due remote-control transport failure and a security rejection; the refusal was respected, no substitute remote command was used.

## Result
**ITEM6=DONE** for nominal private Git source migration/recovery already proven and independently re-checked at the GitHub source. The private inventory and detailed SHA/refs are retained in the restricted recovery evidence and must not be copied to this public Test Hub.

**ITEM13 remains blocked/partial** for five historically divergent GitLab ref writes under explicit security review. Neither that scope nor social publishing is a completion criterion for item 6. No repository histories were overwritten; no public inventory, secret or private branch names are disclosed.
