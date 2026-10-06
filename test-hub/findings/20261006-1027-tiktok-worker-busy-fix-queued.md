# TikTok worker-busy fix — queued session verification
STATUS: RUNNING
DATE: 2026-10-06
SERVICE: anthares-tiktok-render-rootless
SERVICE_ID: srv-db18d3tg1s2s7391l4ng
COMMIT: 00cd4b3991f55ff4f29f63d98fffdb4c0e089cbc
DEPLOY: dep-db2g9vuk1f9s73abq8l0

QA40 proved central/session-status health but the 30 session-test replicas collided on the single Render process lock. Causal fix: session-test now waits up to 240s for the worker lock instead of immediately returning 409. This preserves the single-browser safety boundary while allowing the GitHub matrix to drain through the worker.

Do not launch QA50. After this deploy is healthy, run one allowlisted session-test probe first. If it proves identity, perform one fenced production canary. If it still times out, inspect Render latency/resources and decide whether a second Render instance or a separate read-only verifier is required.

MeshCentral redundancy is now PROVEN in the hub and can be considered closed.
