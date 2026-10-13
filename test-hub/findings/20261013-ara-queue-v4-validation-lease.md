# ARA v4 queue-only validation lease

STATUS: RUNNING
AREA: ara-private-queue-v4-cutover
OWNER: chatgpt-ara-finalization
LEASE_START_UTC: 2026-10-13T17:21:00Z
LEASE_EXPIRES_UTC: 2026-10-13T17:51:00Z

GOAL:
Prove that the current independent private GitHub issue queue is alive after removing Render/Cloudflare control dependencies, then identify the active agent generation before retiring legacy writers.

SAFETY:
- ping/process/task/file inspection only until active generation is proven;
- no desktop interaction;
- no Render/Cloudflare controller reintroduction;
- do not weaken DPAPI/ACL protection.
