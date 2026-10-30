# ARA parallel owner authorization cookie isolation deployed
STATUS: PARTIAL — SERVER FIX PROVEN; SECOND CONNECTOR OWNER CONSENT PENDING
AREA: cloudflare-control / ara-oauth
DATE: 2026-10-30
OWNER: codex ara-owner-cookie-20261030
COMMIT: 88684f7950e99797ed399a8d3943e657c3d45688
SUPERSEDES: test-hub/findings/20261030-lease-ara-parallel-owner-state.md
LEASE: CLOSED
GOVERNANCE: 84905aefc5589d17

## BASELINE_PROVEN
User reauthenticated Anthares Remote — Cloudflare; real capabilities returned ok=true, ara.read and ara.write. Other connector still required authentication; screenshot owner_state_invalid. The single fixed __Host-ara-owner cookie could be overwritten or deleted by a concurrent flow on the same host.

## REPRODUCTION_AND_FIX
Baseline remote run41054110992 reproduced reverse-completion collision: first flow403 instead of302 after second flow completed and cleared the shared cookie. PR1967 merged normally, isolating each encrypted HttpOnly Secure SameSite=Lax host-only cookie by its strict43-character random state. Callback still verifies encrypted state nonce, expiry, pending transaction, PKCE, exact GitHub owner and atomic replay. Only selected transaction cookie is cleared; in-flight legacy cookies remain compatible. No token rotation, permission expansion, protection disabling or new identity used.

## EVIDENCE
Remote validation https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41054259597:27 tests,27 pass,0 fail, including concurrent connectors, legacy rollout and cross-state rejection.
Canonical deployment https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/41054357430 SUCCESS; version27db7e12-d9fc-4974-a957-3fd138cbd3cc; ANTHARES_CLAUDE_BRIDGE_DEPLOY_ACCEPTANCE=PASS and anonymous MCP denied.
Real HTTP two new pending flows returned distinct per-transaction host-only cookies with HttpOnly/Secure/SameSite=Lax and10min expiry. No provider redirect followed, GitHub token obtained, browser cookie written, screenshot code replayed or local work file created. Stateless test pending values discarded.
Existing authenticated connector still returned capabilities after rollout. Vercel and shared-Neon independent compute reserve unchanged.

## LIMITS
Real second connector consent remains pending; initiate a fresh reconnect from its settings. device_connected=false remains the separate Windows transport issue; no command job was enqueued, supervisor changed or second executor launched. AVS item12 not executed.
