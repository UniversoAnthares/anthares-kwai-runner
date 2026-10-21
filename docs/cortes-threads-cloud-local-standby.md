# Threads: cloud-primary, local-standby migration (2026-10-21)

## Invariant

- Primary publisher: Anthares Browser on independent cloud compute, with account identity verification and shared publication lease.
- Standby publisher: existing Windows task "Anthares CORTES Threads Browser Publisher" at D:\AntharsWork\cortes-social-browser-20261020. Preserve it **without deleting its task, profile, files, manifest, or ledger**.
- Keep the Windows fallback functioning during migration because the cloud identity and shared coordination have not been proven.
- Switching priority requires (1) cloud-owned authenticated profile; (2) remote media manifest refresh independent of the Windows host; (3) durable lease and confirmation reconciliation across both publishers; (4) canary URL verified on Threads.
- When cloud is proven, gate the local scheduler before browser initialization so it remains invisible, muted, idle during healthy primary service, and executes only after a fenced primary failure.
- Fail closed on uncertain publication after clicking Post; never automatically publish an uncertain ID again.
- No Browserless dependency. Use the Anthares Browser runtime. Admin/control MCP exclusively Anthares Remote.
- All title/caption strings must pass Unicode integrity checks (UTF-8, no replacement characters, proper Unicode bullet suffix).
- Do not change other CORTES publisher schedules or local fallback tasks during this migration.

## Stage 1: cloud authentication probe

Workflow: \`.github/workflows/cortes-threads-cloud-readiness.yml\`. This read-only job restores the existing encrypted browser state from the canonical Anthares Browser vault, launches isolated Chromium in GitHub Actions, navigates to Threads, and reports only redacted gate results. It intentionally does not upload videos, click Publish, or change browser state in the vault.

A successful GitHub job **only proves that the probe executed**; it does not prove authentication. The explicit \`CLOUD_AUTH_GATE\` value is authoritative. No cut-over until verified.
