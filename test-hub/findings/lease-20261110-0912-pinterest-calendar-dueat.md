# Pinterest Buffer dueAt — leitura autenticada temporária
STATUS: RUNNING
DATE: 2026-11-10 UTC
AREA: pinterest-buffer-readonly-calendar
OWNER: chatgpt-pinterest-0912
BASE_GITHUB_HEAD: a67be60c67fe09916da1a9efaaaa68be28aa0807
TARGET_WORKFLOW: .github/workflows/buffer-cortes-live-calendar.yml
TARGET_BLOB_GITHUB_AND_GITLAB: c0f45620f0c0945845379e252078985d67e183c0
PREVIOUS_FINDING: test-hub/findings/20261110-0847-pinterest-buffer-publisher-restored-publication-pending.md
LEASE_MAX_MINUTES: 30
BASELINE_PROVEN: 2 buffer scheduled Pinterest jobs (remote IDs 6af30eae85810493942e8171 and 6af3114d6202102f59bf7128); last readback 09:10 local, 0 new public Pins. Calendar workflow exists as read-only and disabled_manually. Other publisher remains active; no competing calendar/Pinterest jobs active.
FAILED_AVOIDED: Do not invoke older first-pin-promote workflow pinned to a different Buffer post, do not edit or shareNow live posts, do not create duplicates; preserve official Pinterest publisher state and BWS credentials.
SUCCESS_SIGNAL: Existing Buffer calendar read-only workflow returns the exact dueAt of two scheduled IDs and account queue time without any mutation; afterward restore calendar workflow to disabled_manually.
FAILURE_SIGNAL: HTTP 401/403/429, 500 metadata issue, unexpected identity, lack of dueAt, auth invalid, quota; preserve existing scheduled Pins, cancel blocked job if cota and restore workflow disabled.
TEST_VALIDITY: Use existing Workflow `buffer-cortes-live-calendar.yml` only, permission contents:read, no Neon or Buffer mutation. Never confuse a schedule with public delivery.
NEXT: Temporarily enable read-only calendar, dispatch once, check logs/artifact, restore previous disabled state, close lease.
