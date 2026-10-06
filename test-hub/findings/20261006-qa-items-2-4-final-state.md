# QA items 2-4 final state — production gates and blockers
STATUS: PARTIAL
AREA: tiktok
DATE: 2026-10-06
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37410436742; https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37410921929; https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37410640235
JOB: 112097436967; TikTok reconcile observe; synthetic-controlled-canary
COMMIT: e10bc3a6dbc0b77ea047c5ccd1cb6d37ebf34cb; 741c6ff0cc61093cb432f8f3d277b1ea2e3fb176
SUPERSEDES: none

## Objetivo
Fechar definitivamente, dentro do que o QA pode provar sem fabricar publicação, os itens 2, 3 e 4 da lista operacional: Kwai publish safety, TikTok real canary, and final production adversarial closure.

## Resultado

### Item 2 — Kwai publish
The production-side implementation is PROVEN through the final CHAT2 acceptance: UNCERTAIN/reconcile, explicit prepare/commit phases, media identity, SHA binding, READY gate, fencing, heartbeat, no-PC path and real-publish gate all passed. The acceptance explicitly leaves only the real Kwai publication outside its scope, because that requires kwai-login READY.

The current Kwai login evidence remains PARTIAL: profile/login probes reached the main navigation in the promising routes but no route proved authenticated login. The latest real autologin finding ended before credential submission because no editable account control was found. Do not claim KWAI_REAL_REMOTE_POST=PROVEN.

### Item 3 — TikTok real canary
The controlled MP4 generation is PROVEN, and the Render publisher infrastructure is already proven. The v3 canary did not reach publication_started. Current diagnostics show Render session state was lost after redeploy and central restoration is currently rejected: session diagnostic returned bootstrapped=false, identity_verified=false, ready_for_tiktok=false; central restore returned HTTP 403. A direct central-session request from the newly created diagnostic workflow returned HTTP 401. The allowlisted observation workflow previously returned HTTP 200 with 21 cookies at run 37409026789, proving that the central session existed and that this exact workflow family had authorization earlier. The current rejection therefore blocks session restoration before publication.

No real TikTok post was claimed. Do not claim TIKTOK_REAL_REMOTE_POST=PROVEN.

### Item 4 — final production adversarial closure
The safety contracts are PROVEN. The final CHAT2 acceptance passed all 24 checks, including UNCERTAIN, observation-only reconcile, evidence-gated complete, generation fencing, heartbeat, dedupe-related contracts, no-PC production path, manual real-publish gate and serialized publication. The real-production closure remains conditional on obtaining both real-post proofs.

## Additional causal fixes performed by QA
- TikTok Render /publish now exposes confirmed/remote_id/confirmation_evidence when the publisher emits a remote_id.
- TikTok read-only browser-memory probing was changed to wait for the worker lock instead of immediately returning 409; later concurrent work restored the memory gate in the canary workflow, so that change is retained as infrastructure hardening rather than declared the production gate.
- Android boot harness was hardened to install platform-tools explicitly under ANDROID_SDK_ROOT.
- Temporary session diagnostics established the exact current central-session failure without exposing credentials.

## Final acceptance state
KWAI publish safety: PROVEN; real Kwai post: BLOCKED on authenticated READY.
TikTok media: PROVEN; TikTok publisher: PROVEN; real TikTok post: BLOCKED on current central-session/OIDC restoration.
Adversarial queue/control contracts: PROVEN.
Project-wide final production acceptance: OPEN until independent verification and ledger confirmation exist for both real posts.