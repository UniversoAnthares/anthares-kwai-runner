# Lease — Firebase Test Lab Android secondary
STATUS: RUNNING
AREA: android
DATE: 2026-10-06
RUN: none
JOB: none
COMMIT: none
SUPERSEDES: test-hub/findings/20261006-0854-android-redundancy-candidates.md

OWNER: chatgpt-firebase-secondary
SCOPE: Firebase Test Lab capability/integration only; no Kwai login/session mutation.
BASELINE_PROVEN: gcloud authenticated; universo-anthares ACTIVE; testing.googleapis.com enabled (finding 20261006-0936-firebase-testlab-project-discovery.md).
FAILED_AVOIDED: previous credential blocker is causally removed; do not create a new GCP project.
SUCCESS_SIGNAL: Test Lab device catalog is readable and a minimal Android test can be submitted with results/artifacts, proving independent cloud substrate.
FAILURE_SIGNAL: project/billing/API/device execution rejects a valid minimal test.
TEST_VALIDITY: no Kwai credentials/session or irreversible publication involved.
