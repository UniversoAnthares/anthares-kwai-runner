# Lease: isolated Asaas webhook regression tests
STATUS: RUNNING
AREA: wordpress-payments
DATE: 2026-10-08
BASELINE: anthares-wordpress main 85aa1ed, PR18 branch 42b5d490d8c9af09fa855a8a7bb1d8e3c36d72ce; GitLab hosted PHP lint success pipeline 2927070498.
FAILED_AVOIDED: no production Asaas calls, no webhook deletion, no main modifications, no token disclosure.
SCOPE: add isolated PHP tests and run in GitLab branch CI; review source and peer HEAD before write.
SUCCESS_SIGNAL: tests verify valid stored, corrupt stored, missing encryption, failed persistence, valid first creation, missing token registration guard.
FAILURE_SIGNAL: any false success or syntax regression.
Lease expiry: 30 minutes from creation.
