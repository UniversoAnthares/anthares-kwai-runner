# Anthares-browser proof — 2026-10-13

## Hosted runtime proof

Render service: `anthares-browser-qa-render-v2` (`srv-db6ootl9fdbs73do9sm0`).
QA branch: `qa/anthares-browser-render`.
Final hosted QA commit: `22a056706da74a7ac57b883059f9c134ae4bf017` (includes the loopback-only internal API/result-port isolation contract).

The hosted runtime emitted `ANTHARES_BROWSER_RENDER40_RESULT` with `ok=true`.

All 40 cases passed. Every case independently passed:

- navigate
- wait
- type
- evaluate
- click
- click-effect verification
- real PNG screenshot validation

The same run also passed:

- `restart_profile=true`: localStorage state survived a full stop/start of the isolated browser stack using the same browser profile;
- `novnc_internal=true`: noVNC remained available internally while the browser-control API stayed loopback-only for the hosted proof;
- control API authentication checks before the 40 functional cases;
- CDP bound to loopback.

No GitHub Actions, CircleCI, or user-PC executor was used for this proof.

## Vault isolation / durable state

The Cloudflare browser-state vault uses separate state slots for service-local cryptographic authorities:

- runtime: `/browser-state/runtime`
- control: `/browser-state/control`

`infra/anthares_runtime_mesh_vaulted.py` binds the slot from `ANTHARES_BROWSER_STATE_AUTHORITY` and rejects unknown authorities.

Operational service configuration:

- `anthares-x-render-worker-v3`: authority `runtime`, vault URL `/browser-state/runtime`;
- `anthares-remote-control`: authority `control`, vault URL `/browser-state/control`.

Control-side persistence proof after service replacement emitted:

`ANTHARES_BROWSER_PERSISTENCE healthy=True restore=restored persist=True proven=True authority=control`

Runtime-side proof first emitted `healthy=True restore=empty persist=True`, creating state in its isolated slot. After instance replacement, the persistence-status route returned HTTP 200 without the `browser_persistence_unproven` diagnostic that is emitted by the current implementation whenever `persistence_proven` is false. This is consistent with successful restore on the replacement instance.

## Current proof boundary

Proven:

- Chromium startup and self-recovery;
- real CDP operations;
- API authentication boundary;
- navigate/wait/type/evaluate/click/screenshot;
- 40/40 hosted cases;
- browser profile restart persistence;
- internal noVNC isolation;
- separate runtime/control vault authorities;
- control-slot restore across service replacement;
- no host-desktop fallback.

Not claimed by this document:

- a currently authenticated Kwai account;
- a real Kwai publication.

Authentication remains fail-closed: absence of a login prompt is not accepted as authentication proof.