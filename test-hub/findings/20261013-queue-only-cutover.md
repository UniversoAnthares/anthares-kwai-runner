# ARA queue-only cutover

STATUS: RUNNING
DATE_UTC: 2026-10-13

Goal: remove Render and Cloudflare HTTP control dependencies from the Windows Anthares Remote supervisor and prove the private GitHub issue queue remains operational after the cutover.

Expected proof:
- supervisor state reports `mode=issue-queues-only`;
- `render_required=false`;
- `cloudflare_required=false`;
- `http_control_enabled=false`;
- a fresh `ping` job in `UniversoAnthares/anthares-ara-queue` receives an `ARA_RESULT_B64` result with `ok=true` and `output=pong` after the task restart.
