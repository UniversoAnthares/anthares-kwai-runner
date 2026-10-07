# Lease real workload GitLab failover
STATUS: RUNNING
AREA: architecture
DATE: 2026-10-07
BASELINE_PROVEN: GitLab hosted pipeline 2924284172 passed provider router acceptance; anthares-control production self-test passes five fail-closed cases.
FAILED_AVOIDED: no mirror CI, no GITHUB_MIRROR_URL, no force-push, no competing cloudflare-control deploy while this lease only changes CI/execution adapters.
SUCCESS_SIGNAL: GitLab equivalents exist for portable operational workflows, at least one real workload executes successfully on GitLab hosted runner, quota/unavailable state has an automatic evidence path into provider decision, and unsupported Android/KVM jobs are explicitly gated.
FAILURE_SIGNAL: translated workload cannot run on GitLab runner, secrets are required but absent, or failover can write with divergent checkpoint.
TEST_VALIDITY: pipelines must execute repository code and emit explicit success; harness/config errors are INVALID/PARTIAL, not provider failure.
LEASE: expires in 30 minutes.
