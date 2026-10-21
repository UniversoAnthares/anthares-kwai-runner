# Anthares execution provider contract

GitHub remains the canonical repository and history source. This file defines the fixed execution policy used by Anthares routing.

## Non-negotiable execution rules

- Remote device control uses **Anthares Remote only**. No other remote-control product is an operational fallback.
- Browser automation uses **Anthares Browser only**. Browserless is superseded and must never be selected or described as Anthares Browser.
- Render, TinyFish and CircleCI are retired from all operational paths. Their former responsibilities must be migrated.
- A quota-exhausted provider is `BLOCKED_QUOTA`, not `DOWN`. Routing migrates the workload instead of trying to repair healthy code.
- An Anthares-owned component that fails while its provider quota is available is a repair target before migration.
- GitHub Actions on private repositories is treated as quota-constrained until a fresh successful private-repository run proves availability. Public-repository Actions remain independently eligible.
- GitLab CI is permanently excluded from **automatic execution selection** while quota is blocked (`ci_quota_exceeded` reconfirmed on 2026-10-21). The independent GitLab Issues recovery queue for Anthares Remote remains usable; it is **not** a CI runner.
- Codeberg holds an independent Git mirror but is **not a CI runner** while repository `has_actions=false`; only a fresh verified equal `main` SHA makes the mirror eligible as a recovery source. Source mirroring is separate from video publishing.
- Cloudflare products are tracked separately by product. Workers Builds, Workers runtime, Durable Objects and Browser Rendering must never share one aggregate status. Browser Rendering is quota-sensitive and cannot be used as a substitute for Anthares Browser.

## General hosted CI

Current priority for workloads that genuinely require hosted CI:

1. GitHub Actions on public repositories, while live status is READY.
2. Harness, while READY.
3. AppVeyor, while READY.
4. Floot, while READY and technically compatible with the workload.
5. Cloudflare Workers Builds for Worker-compatible build/deploy workloads only.
6. GitHub Actions on private repositories only after a fresh quota-success proof.
7. Codeberg Forgejo Actions only after repository Actions is enabled, a permitted runner is provisioned, and a real job plus publication-specific OAuth/Neon OIDC compatibility is proven. Currently ineligible.

GitLab CI is intentionally not on this list. Codeberg Git mirroring alone does not grant CI execution.

The router must distinguish repository visibility because GitHub quota behavior differs between public and private workloads.

## Anthares Remote

Anthares Remote is the only supported remote-control route. Health requires a fresh heartbeat plus a successful command round-trip. A heartbeat alone is insufficient. Queue state must expose queued, leased and uncertain counts.

When Anthares Remote fails:

1. classify provider quota separately from Anthares code/runtime health;
2. repair Anthares Remote when its own bridge/agent/control path is faulty;
3. migrate an external dependency when that dependency is quota-blocked or retired;
4. use an implementation agent such as Codex, Kilo or Work only for work that benefits from a coding/browser agent and whose connector is currently available;
5. require manual owner action only for security boundaries, account authorization, billing/plan decisions, CAPTCHA/MFA or controls that cannot be automated legitimately.

## Anthares Browser

Anthares Browser is the canonical browser subsystem. Its implementation may use whichever eligible infrastructure is selected internally, while its external identity remains `anthares-browser`.

Browserless, TinyFish and Cloudflare Browser Rendering are not alternate names for Anthares Browser. Browserless and TinyFish are retired. Cloudflare Browser Rendering may be an infrastructure component only when quota is available and the Anthares Browser architecture explicitly selects it; it is never a direct operational fallback.

## Android / Kwai

Android execution remains a separate capability. A device/emulator can be selected only when the current workflow explicitly permits that executor and current health is READY. Desktop-local Android tooling is not promoted into a second remote-control system.

## Failure classification

Every failure is classified before retry or migration:

- `ANTHARES_COMPONENT_FAILURE`: repair the Anthares component first.
- `BLOCKED_QUOTA`: migrate the workload to another eligible provider; do not retry repeatedly.
- `PROVIDER_DOWN`: fail over after checkpoint/lease safety checks.
- `AUTH_REQUIRED`: use an authorized session flow; manual owner action only when unavoidable.
- `RETIRED_PROVIDER`: migrate permanently and delete active routing references.
- `UNSUPPORTED_CAPABILITY`: use another provider or implementation agent whose capability matches.
- `UNKNOWN`: fail closed until a bounded probe identifies the class.

After a possible publication, reconciliation always precedes retry.

## Regression rule

Before every new implementation round, re-check previously completed phases for regression. A prior phase reopens only when fresh evidence shows a failed invariant.

Machine-readable sources: `ci-hub/executor-routing.json` and `ci-hub/quota-status.json`.
