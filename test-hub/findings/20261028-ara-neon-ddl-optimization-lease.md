# ARA Neon CU-hour reduction — SQL cold-start optimization
STATUS: RUNNING
AREA: queue / ara-neon-cost
DATE: 2026-10-28
OWNER: ChatGPT GPT-6
BASELINE_PROVEN: Vercel production deployment dpl_2ew3WQvu8W2n3utFUKHMPGHRQ7Rb, commit 4494ea971df658b5ae934c3c233936346cfdd678; ARA C8 active; Neon schema catalog checked.
FAILED_AVOIDED: no modification of job states, SAFE_RETRY, leases, OAuth replay, agent binary or production deploy. No schema creation on every HTTP request.
SUCCESS_SIGNAL: readback exact patch and confirmed presence of constraint/index/table in production; static syntax and review before production deployment.
FAILURE_SIGNAL: concurrent HEAD changes, missing schema, static syntax failure, or any altered lease/replay invariant.
TEST_VALIDITY: GitHub and GitLab blobs for both target paths match before patch; production SHA retained separately for rollback.
EXPIRES: 30 minutes from acquisition. Release by successor finding.
