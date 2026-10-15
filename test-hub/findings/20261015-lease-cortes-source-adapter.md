# Lease — CORTES source adapter

STATUS: PROVEN
AREA: cortes-source-adapter
DATE: 2026-10-15
OWNER: chatgpt-cortes-source-adapter
BASE_KWAI_RUNNER: 68d88005ba038696cbfe259b72d216ce453fadfd
SCOPE: Connect the canonical daily live/regular-video source-cycle policy to the existing WordPress/CORTES legacy blocker and registry adapter. No publication tests. No method 1+2 test. No method 3 implementation/test.

## Guardrails
- Preserve existing live publication/runtime behavior.
- Ordinary-video fallback: >15 minutes, never Shorts, never YouTube.
- One locked source per day; do not advance until its CORTES lifecycle is terminal.
- GitLab mirror is historical/stale relative to GitHub and must not be blindly mirrored.

## Located legacy runtime
The previously missing bridge was located in `UniversoAnthares/anthares-wordpress`:
- `anthares-clipper/cortes-control.php`
- `anthares_cortes_current_blocker()` and `/anthares/v1/cortes/state`
- the existing legacy `/anthares/v1/clipper-live/registry` bridge
- the live lifecycle whose terminal state is `stage=completed` after generated files have been removed.

## Implemented
WordPress repository:
- commit `92c2bd31ce11e8ce94b5de4c2452b268b30681bd`: added `anthares-clipper/cortes-source-adapter.php`.
- commit `aa662d87792466983c62d383fac5f8a992ae5e3f`: loads the adapter from plugin 2.7.3.
- canonical cycle is persisted via `/anthares/v1/cortes/source-cycle`.
- eligible ordinary-video inventory is persisted via `/anthares/v1/cortes/regular-sources`; server rejects `<=900s` and Shorts.
- `/cortes/state` projects the canonical locked source as the blocker.
- `/clipper-live/registry` projects exactly the canonical source to the unchanged legacy worker, including a synthetic legacy-compatible row for ordinary videos.
- YouTube is dynamically suppressed while `source_kind=regular_video`; persisted network configuration is not destroyed and therefore returns automatically for live sources.
- old/legacy lives can be replayed in a new canonical cycle without being immediately reclassified as legacy by discovery.

Clipper repository:
- commit `7da3ace927a6cc981314b5b2676bfc87b2a8adaa`: added discovery/selection-only `cortes_source_adapter.py`.
- commit `2dc52f4b3a0cdb5ceac95d07edf35d9c0d90e7b1`: wired source selection after the existing streams discovery workflow.
- it holds a source across midnight until CORTES reaches terminal/deleted state and then delegates next-source selection to `cortes_cycle_policy.py`.

## Validation
Private-repository GitHub Actions could not start a runner: the WordPress syntax job and private Clipper discovery job both returned `steps=[]`, `runner_id=0`. This is runner/quota infrastructure failure, not an observed test failure in the code.

The production validation therefore reused the already proven public-runner + GitLab secret-bridge deployment path. One-shot workflow commit: `b0967087553a21ed84a00a584d859b5e304992b7`.
Production run: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/38765346493
Result: SUCCESS.
The job:
- retrieved the exact WordPress commit `aa662d87792466983c62d383fac5f8a992ae5e3f`;
- reached the real Hostinger installation;
- PHP-linted the complete plugin before swap;
- atomically deployed the plugin;
- verified through WP-CLI that plugin 2.7.3 is active, the adapter function is loaded, and `/cortes/source-cycle`, `/cortes/regular-sources`, `/cortes/state`, and `/clipper-live/registry` are all registered;
- completed the public `/cortes/` HTTP smoke successfully.

The temporary deployment workflow was removed immediately afterward in commit `8ba7ef2f5897a9e9283ead3252d3acc2b51fecae`.

## Result
The limitation reported in the previous round is resolved: the canonical daily live/ordinary-video cycle is now connected to the production WordPress/CORTES blocker and to the unchanged legacy registry/runtime contract. This round did not run a social publication or media extraction test.

## Explicitly pending
- publication/extraction test for methods 1+2;
- method 3 redundancy implementation/test.
