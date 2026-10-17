# One-time full social replay activated; YouTube history retained
STATUS: PROVEN
AREA: queue, wordpress-deploy
DATE: 2026-10-17
COMMITS: clipper d1098ed6e03010f2ab5952c4534458fdc7a4fbd8; WordPress 08e87ffa87fc04c7b1d75d0b77e228ef5c1f278d and 13c0c737f51cfbbf845249a1821f2ff45712e53c
SUPERSEDES: test-hub/findings/20261017-2144-lease-cortes-onetime-replay.md
LEASE: CLOSED

## Explicit owner request
Restart the entire social source queue only once, from oldest live; retain YouTube publication history, skip legacy lives1..137 on YouTube, resume eligible YouTube sources at138; begin adding other social destinations. This explicitly authorizes the otherwise-forbidden mid-day source reset. No test publication requested.

## Activated state
No CORTES workflow was in_progress; no stored pending masters existed. Full raw cycle/registry/YouTube-history backup saved in private account maintenance directory before mutation. Previous current source144 remained archived/completed.
Source cycle generation1 active; request_id owner-restart-20261017; 154 frozen ordered live IDs; cursor0; first source b6gL9plY_6w, title A Poetica de Aristoteles Parte1, chronological_index1. replay_once records the generation and is consumed at live-inventory completion. Repeating the same activation request is idempotent; no automatic reset hook was installed.
YouTube history contains138 sources:137 legacy IDs plus already confirmed source144 (1nJlreUmWKg). IDs are preserved independently of mutable ordinal positions. First source YouTube disallowed; Kwai enabled; configured YouTube setting retained for automatic eligibility restoration. Source138 SJej0kuqELk allowed; source144 denied. No YouTube history erased.
Active source long phase analyzed count0 because no enabled long destination; short phase pending. This allows Kwai short generation without rendering/distributing YouTube longs during the legacy replay.
Final cycle serialized SHA256 15ba8c42638afb4fb9674ee32fe44801a7d99bc27619e68c79e521a83ed6b650.

## Code protections
Canonical policy adds one-shot replay initialization and generation-scoped metadata, permanent completed-source IDs, chronological selection and replay completion marker. Short plan keys, segment IDs and filenames include generation; long recovery files include generation. Producer skips unavailable long destinations and checks YouTube policy again before credentials/upload; non-YouTube longs register via CORTES instead of the YouTube queue.
WordPress source reset archives old state, keeps replay progress safe from discovery reapplying legacy flags, and computes YouTube eligibility from durable server-side history. YouTube media-register rejects excluded sources; media-pending hides excluded sources. Completed YouTube sources are retained as history before cleanup. Temporary dynamic suppression cannot accidentally persist as a disabled YouTube setting when another network is edited.
Concurrent main commit ec80c715 (short score threshold4 and Anthares title suffix) was freshly read, merged via fast-forward/stash reconciliation, retained, and regressions rerun before publishing.

## Other networks: implemented foundation, not live publication claim
Catalog and authenticated /cortes/destinations cover14 platforms with canonical short/long classes and daily caps. Shared master SHA256 and per-platform/account idempotency, attempts, remote confirmation and required-destination state are represented independently. Multi-account callbacks cannot complete other accounts; cleanup waits for required account confirmations. Disabled or unconnected destinations remain pending_connection and do not masquerade as working adapters. Existing adapter names for TikTok/Instagram/Threads/X recorded; other adapters remain pending. Medium remains article/embed-only, disabled, not MP4 upload.
Only Kwai currently enabled for replay. Additional network authentication, adapter wiring/limits and real publication acceptance are still pending; no claim all14 platforms are operational.

## Validation
41 focused Python tests passed; PHP lint passed on all6 deployed files plus activation script.17 isolated replay/destination/account checks passed, plus network settings preservation check. Live modules loaded with14 catalog entries.
Actual authenticated HTTP checks passed: /cortes/state first source b6gL9plY_6w, generation1, Kwai enabled, YouTube disabled; /cortes/destinations returned14; negative media-register request for legacy source rejected HTTP409 youtube_source_already_published before any attachment/upload operation. Temporary verification app password removed in finally.
Deployment used fresh byte hashes, private backups, staged new dependencies first and atomic per-file replacement. Manifest CRLF normalized only after confirming PHP hashes matched; no integrity checks bypassed. GitLab histories left unchanged.
No media download/render, social post, workflow dispatch or deletion performed by activation/verification. This proves configuration and exclusion gates, not a new end-to-end published post.
