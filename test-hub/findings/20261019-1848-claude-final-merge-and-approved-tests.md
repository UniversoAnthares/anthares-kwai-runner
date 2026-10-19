# Claude integration merged; approved regression execution implemented
STATUS: PARTIAL
AREA: ara-mcp-claude-deploy / claude-session
DATE: 2026-10-19
SUPERSEDES: 20261019-1842-lease-claude-final-deploy-merge.md; 20261019-1220-lease-claude-final-integration-tests.md
LEASE_STATE: CLOSED

## Completed and independently verified
PR162 merged into main at 4385a0f49f4ce3bcc9bd05f1dd1689e61d3324e9. Operational docs PR191 merged at 001c47e4aa067b90f58ea747baac3fa3ab37c87a. Concurrent main history was preserved, with no forced update and no CORTES/Android/SSH behavior changes.

Worker f69e09b4-4ef2-48f5-acaf-fed056d462e2 is deployed with protected existing secrets preserved; previous version 24ffad76-20a0-4911-b6c9-465ad1b135b2. Exact approved test source pin: 30217080974912cbfc049072b844f473a69c0e27. Live health returned ok=true, control_ready=true, device_connected=true and oauth_owner_code_mode=github_owner_identity. GitHub identity is the canonical authorization method; email delivery is retired as a dependency rather than falsely reported repaired.

New tool run_tests uses existing github.write consent and accepts only suite=mcp-regression plus a UUID request_id. It rejects arbitrary commands/source injection/unknown suites, consumes a one-use request, extracts only the reviewed pinned source from Git, serializes processes with a mutex and records append-only Test Hub RUNNING/result findings. It reports tested SHA, counts and job ID; it does not execute caller-provided code or grant ara.write.

Actual fixed runner proof under renewed current-time lease: Remote job 2bc5586aa23426b407a166a33fe6cb67 returned ok=true, tested_source_sha=30217080974912cbfc049072b844f473a69c0e27, passed=26, failed=0, capabilities_passed=true, exit_code=0. Tests include insufficient-scope refusal and existing ChatGPT contract. Earlier stale-time lease was superseded; its resumed tests are not the final current-lease proof.

## External acceptance blocked by free-account quota
The dedicated visible browser restored the owner's authenticated Claude conversation. Attempting to send the actual run_tests prompt failed before model execution: UI showed 'Você está sem mensagens gratuitas até 18:00' and the five-hour limit dialog. No tool call was issued and no run_tests-through-Claude success is claimed. Do not keep retrying before quota reset, upgrade to paid service or use another identity to bypass the limit.

Previous owner OAuth, 20-tool catalogue, Remote status and actual Claude GitHub read/write/draft PR164 acceptance remain proven by 20261019-1216-claude-mcp-real-acceptance-proven.md. The sole new acceptance step is a real Claude run_tests invocation after quota becomes available. Request UUID prepared but not sent successfully: 4c313d16-7057-4b45-bf23-c76e09dfe62a. Use the normal conversation https://claude.ai/chat/1f73a1f0-743c-4fc0-871c-f764fd991afe; never invent a success result. Fresh lease required for later acceptance.
