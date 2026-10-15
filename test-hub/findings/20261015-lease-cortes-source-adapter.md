# Lease — CORTES source adapter

STATUS: RUNNING
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
