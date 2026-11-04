# C8 wake notifications — Hostinger integration contract
STATUS: SOURCE CORRECTED; LIVE C8 DEPLOYMENT NOT CLAIMED
DATE: 2026-10-29
PR: #1808

This revision supersedes the Cloudflare WSS/HMAC deployment instructions
previously in this document. Cloudflare prototype files remain isolated;
do not deploy them as a second notifier. Reuse the Hostinger sender of PR1815.

## Deployed broker examined
Hostinger anthares.us public_html/ara-notify/index.php:
SHA256 537c6dfc5b54163b9a1cd7180e21dba21ca3bca05e5a33b236e0e2dbfe5b649c.
Read through existing SSH after authenticated hPanel File Manager connection
reset. Broker source was not modified. Config hashes and state live privately
in domains/anthares.us/.anthares-ara-notify outside public_html.

## Exact receive protocol
Fixed HTTPS endpoint: https://anthares.us/ara-notify/index.php
It is HTTP JSON long polling, NOT WebSocket/SSE/HMAC.
Use a separate listener token via X-Anthares-Notify-Key: <listener secret>.
Authorization: Bearer <listener secret> is also accepted by PHP.
If Authorization is present it takes precedence over the custom header.
Token syntax: [A-Za-z0-9_-]{32,128}; SHA256 compared with listener_sha256.
Never send the C8 device bearer or publisher token to this receive endpoint.
The existing Hostinger listener.token is a protected secret reference;
provision it to C8 through the authorized protected-secret mechanism, never
through Git, task arguments, URLs, screenshots or ordinary logs.

Initial GET:
?action=health&device_id=DESKTOP-FTDK0HP
200 JSON {"ok":true,"protocol":"ara-wake-v1","sequence":N,"role":"listener"}.
After success, scan original queue immediately to cover jobs predating subscription.

Then GET repeatedly (one in flight):
?action=wait&device_id=DESKTOP-FTDK0HP&since=N&seconds=20
200 JSON {"ok":true,"protocol":"ara-wake-v1","sequence":M,"wake":true|false}.
M>N and wake=true: coalesce one queue-scan hint, then use M as cursor.
Unchanged sequence/wake=false: idle long-poll timeout, not a command failure.
Broker permits seconds1..25 (default20), nonnegative decimal since <=18 digits.
C8 uses20s and25s client deadline. Replies are bounded to512 bytes, strict
schemas; unknown fields, duplicates, malformed JSON and regressing/inconsistent
cursors fail closed. On broker restart/reconnect, new health resets cursor
and forces a canonical scan; sequence is not a job ID or execution receipt.

PHP failures: bad auth401; wrong device404; wrong method405; invalid cursor/
wait400; state unavailable/invalid503. Do not log credentials or raw bodies.
Redirects are never followed. Auth401/403 or quota402/429 ends this subscriber
attempt immediately; original polling continues. Other transport failures use
bounded backoff2..33s, with original polling restored immediately.

## Publisher interoperability (single sender only)
POST https://anthares.us/ara-notify/index.php?action=signal
X-Anthares-Notify-Key: <independent publisher secret>
Content-Type: application/json
Body exactly {"device_id":"DESKTOP-FTDK0HP"}.
202 JSON {"ok":true,"protocol":"ara-wake-v1","sequence":N}.
This increments a broker counter under a file lock; no job content is stored.
Existing PR1815 notifier copied unchanged into this draft to avoid a competing
Cloudflare emitter. Enabled only via ARA_WAKE_NOTIFY_ENABLED=1, default OFF;
ARA_WAKE_NOTIFY_SECRET is publisher-only. Send once after Neon commit,
900ms timeout, no retries; notification failure does not undo/recreate a job.
202 means broker recorded, never device delivery or command completion.

## C8 integration and unchanged guarantees
ANTHARES_WAKE_ENABLED=1 (default OFF) additionally requires protected
ANTHARES_WAKE_LISTENER_TOKEN with the independent listener credential.
No new Windows process, service, queue or spool. 2-second empty polling when
disabled/offline;12-second safety scan when broker is healthy to catch lost
notifications before minimum31s command expiry. Existing60s heartbeat,
executionSemaphore/global MAX_CONCURRENT, GitHub/GitLab processors,
canonical leasing, idempotency, result replay, SAFE_RETRY/UNCERTAIN unchanged.

## Deployment boundary / item5
Build/test exact candidate SHA and Windows hash in the existing offline CI.
Do not merge this old branch wholesale over concurrent production changes.
Reconcile notifier with PR1815 and the effective deployed controller:
PR1815 recorded that the Cloudflare gateway calls the Vercel reserve, while
its sender was deployed only to primary. An installed primary sender is not
proof of notification after INSERT in the effective reserve controller.
Provision listener secret privately to the existing C8 process, preserve
supervisor/last-good binary, then opt in only after authenticated broker
acceptance and one harmless canonical roundtrip with no duplicate execution.
Rollback flag OFF restores original polling. No production cutover occurred
in this source-only correction. Heartbeat60s still prevents a claim of idle
Neon autosuspend/CU savings; those are outside this task.

Live read-only HTTPS health from Hostinger during this inspection returned403,
before a protocol health receipt. No signal was sent and no state was written.
This is NOT proof that listener authentication or the complete integration
works live; investigate network/CDN versus application rejection without
weakening protections or changing identities. File Manager ERR_CONNECTION_RESET
and this403 are distinct observations.
