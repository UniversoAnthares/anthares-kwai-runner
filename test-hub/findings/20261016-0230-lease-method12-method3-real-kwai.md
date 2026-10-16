# Lease: method 1+2 + method 3 real Kwai canaries
STATUS: RUNNING
AREA: kwai-publish
DATE: 2026-10-16
OWNER: chatgpt-method12-method3-canaries
LEASE_UNTIL: 2026-10-16T03:30:00Z
BASELINE_PROVEN: method 1+2 authenticated acquisition and remote processing passed in GitHub Actions run 38840185597; METHOD12_AUTH_METADATA=PROVEN, METHOD1_PARTIAL_EXTRACTION=PROVEN, METHOD2_REMOTE_EDIT=PROVEN. Method 3 authenticated full-temporary acquisition/process/delete passed in run 38841083860. Canonical Kwai routing remains physical_android -> memu_android, with GitHub Android experimental only.
FAILED_AVOIDED: do not use unauthenticated YouTube acquisition; do not use retired Browserless/TinyFish/Render/WinRemote/MeshCentral; do not route normal Kwai publication to GitHub Android; do not republish any STARTED/COMMITTING/UNCERTAIN job; recover current Android transport before failover.
SUCCESS_SIGNAL: two distinct real Kwai posts on @lucasrosalem, one produced by method 1+2 and one by method 3, each independently verified with public permalink/remote ID and durable queue/ledger confirmation; method 3 additionally proves the full temporary source is deleted only after the final master exists and is verified.
FAILURE_SIGNAL: no eligible authenticated Kwai executor after allowed transport recovery, identity mismatch, queue/lease/dedupe rejection, publication uncertainty, or inability to obtain independent public post identity.
TEST_VALIDITY: acquisition tests require a real YouTube source and valid media bytes; publication tests are valid only after exact @lucasrosalem identity proof immediately before mutation and a clean dedupe/lease state. Harness failures do not count as publication failures.
