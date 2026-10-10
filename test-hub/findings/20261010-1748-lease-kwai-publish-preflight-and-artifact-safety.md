# Lease: Kwai publisher early control-version gate and diagnostic artifact hygiene
STATUS: RUNNING
AREA: kwai-publish
DATE: 2026-10-10
OWNER: chatgpt-publicacao-anthares-turn4
LEASE_UNTIL: 2026-10-10T18:20:00Z
HEAD_BASELINE: daba3681efc84c24e6ea6a869a1949b2645b73d0
RESOURCES: .github/workflows/kwai-queue-publisher.yml; tests/test_kwai_queue_preflight_contract.py
BASELINE_PROVEN: Queue contract requires Cloudflare control v16, lease_generation and canonical source_id/source_start/source_end. GitHub run 38062568151 spent Android emulator setup and failed at Run canonical Kwai queue publisher. Source workflow has no early control-version preflight and uploads kwai-session.enc as a public-repository artifact.
FAILED_AVOIDED: No Android login reruns, no video publication, no lease claim, no Cloudflare deploy, no session manipulation. Existing 20261010-kwai-publish-cloudflare-version-preflight-lease expired at 15:07:20Z.
SUCCESS_SIGNAL: Static test on exact new SHA confirms control v16 + persistent_state + queue_bound + pc_fallback=false gate before vault/KVM/Android, and no encrypted session artifact upload. The preflight must fail closed before emulator on incompatible control.
FAILURE_SIGNAL: Workflow syntax/contract invalid, any emulator step preceding preflight, or session file included in public artifacts.
TEST_VALIDITY: Static-only tests cannot prove deployment or real publication; do not claim real post without URL and independently verified lucasrosalem identity.
SUPERSEDES: none
