# CHAT 2 item 4 — final deduplication closure
STATUS: PROVEN
AREA: kwai-dedupe
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37407161986
COMMIT_IMPLEMENTATION: 39c3df598d7d0ed4c1095e5a6a22923026aa58cf
SUPERSEDES: test-hub/findings/20261006-0305-lease-kwai-control-dedupe-sha-final.md
LEASE_AREA: kwai-control-dedupe-sha-final
LEASE_CLOSED: 2026-10-06T03:06:00Z

Final non-real dedupe scope is closed.

Previously PROVEN barriers retained:
- exact job/dedupe_key;
- positive temporal overlap on same source_id;
- touching intervals allowed;
- different source_id not conflated;
- UNCERTAIN remains protected;
- canonical source interval fail-closed before future publication.

New secondary barrier:
- normalized 64-hex media_sha256 deduplicates identical media within the same platform even across different source IDs/intervals;
- SHA comparison is case-normalized;
- failed jobs permit intentional retry;
- other platforms are not conflated;
- serialized concurrent equivalent enqueues result in one new job + one deduplicated result.

Five-way acceptance run 37407161986 is 5/5 green.

Deployment note: central deploy workflow was repaired from obsolete v12 validation to v16, but deployment run 37407186640 stopped before Wrangler because repository CLOUDFLARE_API_TOKEN is absent. No partial deployment occurred. This does not reopen CHAT2 item 4's non-real acceptance scope; production activation of this controller snapshot is an infrastructure deployment prerequisite and must not be misreported as deployed.
