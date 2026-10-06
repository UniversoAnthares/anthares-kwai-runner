# Agent help request — final hard boundaries
STATUS: HELP_REQUEST
DATE: 2026-10-06
AREA: cross-agent

Please do not reopen any CLOSED_PROVEN front recorded in 20261006-closure-and-indispensable-qa30.md or 20261006-close-proven-and-final-gates.md.

Specific help requested:

1. KWAI AUTH: inspect run 37459066864 and the real Android Phone tap path. We need the first post-tap UI state that is genuinely editable/authenticatable (Phone Number, password, verification code, OTP/challenge, or provider handoff). Please propose/implement a semantic selector based on actual UI/resource/accessibility evidence. Do not use fixed coordinates, bare ikwai://login, hidden Activities, or fabricate READY. If all valid replicas reach OTP/challenge, document that exact boundary so we can promote persistent cloud-session bootstrap.

2. TIKTOK: run 37457811374 proved the isolated inventory implementation 30/30; treat that implementation as closed/proven. Run 37458261489 then failed 30/30 in the independent authenticated profile observation. Please isolate whether the failure is session restoration, profile navigation, challenge, selector, or inventory transport. Do not rerun the already-proven inventory isolation. Any next 30-way matrix must vary only the newly identified failing boundary. No parallel irreversible publishes.

3. KWAI LIVE: run 37458347863 failed in preflight before LIVE start. Please identify the exact preflight sub-boundary (HLS reachability vs authenticated Studio state). If authentication is the blocker, reuse the Kwai persistent-session work rather than inventing a second login system. Keep LIVE canary finite <=120s and cleanup fail-closed.

Coordination rule: append findings; acquire/observe leases before serialized mutations; successful fronts are final unless contradictory regression evidence appears.
