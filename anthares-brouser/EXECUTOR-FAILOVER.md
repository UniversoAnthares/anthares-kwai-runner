# Anthares Browser — executor failover policy

Anthares Browser is the only supported browser-automation surface. Provider executors are backends behind that surface and never become competing browser products.

## Current order

1. Anthares Browser persistent runtime on approved Anthares infrastructure when its readiness contract proves Chromium running, durable state restored and `host_desktop_fallback=false`.
2. GitHub Actions public hosted Chromium for bounded/read-only or one-shot browser jobs when public Actions is currently quota-eligible. The job must load the canonical `browser-state/runtime` vault state and use the same identity gate as publication.
3. Private auxiliary paths, including Codespaces, only after their authorization and quota gates are proven for the current round.

## Ineligible providers

- Browserless: retired and replaced by Anthares Browser.
- Render: retired.
- TinyFish: retired.
- CircleCI: retired.
- GitLab CI: ineligible while the current quota probe reports `ci_quota_exceeded`.
- Cloudflare Browser Rendering: ineligible while its Browser Rendering quota is exhausted; this does not imply that Cloudflare Workers or Durable Objects are unavailable.

## Failover rules

Classify the failure before changing executor:

- Anthares component defect, with provider capacity available: repair the Anthares component first.
- Explicit provider/quota exhaustion: select the next currently eligible backend.
- Authentication/account boundary: fail closed and require the smallest authorization action available.
- Publication outcome ambiguity: reconcile; never replay the publication boundary.

Every backend must use the same canonical session authority, account gate, lease/dedupe contract and evidence format. The user's PC is administration/recovery only and is never a browser execution fallback.

## Operational proof

A backend is eligible only after a current practical run proves browser launch/navigation, exit status and redacted evidence. Historical success is recorded as historical evidence and does not override a current quota or readiness failure.
