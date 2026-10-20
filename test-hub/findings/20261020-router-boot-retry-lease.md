# Anthares free Claude Code router inference timeout recovery
STATUS: RUNNING
AREA: anthares-collab-router-bootstrap
LEASE_OWNER: ChatGPT/collab-router-bootstrap-repair
START_UTC: 2026-10-20T01:57:17.224Z
EXPIRES_UTC: 2026-10-20T02:57:17.224Z
REPO: UniversoAnthares/anthares-kwai-runner
BRANCH: claude/collab-router-bootstrap-retry-20261020
BASE_HEAD: 970cf4b71f983b9ffc6a13423d586d4b6e480527
BASELINE_PROVEN: 39352658418 Claude Free direct request complete+result success; 39355953473 issue-origin authenticated dispatch proof; 39355978335 owner issue binding passed and all three Gemini free model probes passed, but gateway inference probe timed out after 40s (ROUTER_INFERENCE_FAILED_HTTP_0, transport TIMEOUT).
FAILED_AVOIDED: do not re-dispatch issue #227 or alter its claim, do not retry actual nonidempotent task blindly, do not add paid providers; do not relax bot owner binding; only retry the harmless 9Router canary probe on timeout with bounded requests.
SUCCESS_SIGNAL: mocked timeout-first recovery unit test passes, existing tests pass; GitHub CI passes; in new benign owner issue real run router inference returns real generated text and Claude Code produces artifact; completion comment returns link.
FAILURE_SIGNAL: model quota errors after bounded retry; CI error; duplicate issue #227 dispatch; unauthorized actor; absent generated text.
TEST_VALIDITY: CI tests and node-check only prove implementation; must run a new issue-ID canary after merging and validate result. Keep real probe timeout faults distinct from authorization and content errors.
PEER_CHECK: GitHub bootstrap blob == GitLab main blob 5d47a47c967d4413bdfe38aaba278e0594e6ff3d; relevant source not changed by main peer.
SCOPE: tools/anthares_free_claude_bootstrap.js + focused tests + Test Hub, no Cloudflare OAuth or WordPress/CORTES changes.
