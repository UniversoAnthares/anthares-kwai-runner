# AH-03 Cloudflare control plane
DATE: 2026-10-10
ORIGIN: Cloudflare v16 control and remote console chats.
OBJECTIVE: restore live queue-fencing-v16 without resetting queue or compromising credentials.
EVIDENCE: finding 20261010-1859-cloudflare-v16-remote-console-partial.md: /health at 2026-10-10T18:49:16Z returned version=2026-10-05-no-pc-confirmation-v12, persistent_state=true, queue_bound=true, pc_fallback=false. Historical Test Hub PROVEN v16 version ID 1a25c85d-aea3-4bc9-8a8b-5fcedef7abcd is not current live proof. Browserless independent health read attempted in this round and failed (blocked function / scraper HTTP 500); no deploy.
OWNER: prior Cloudflare remote-console agent closed PARTIAL; current deploy owner unverified; coordinator read-only.
DEPENDENCIES: authenticated Wrangler 4.149.0 through authorized background administrative channel, verified target account, exact v16 SHA, independent public /health.
LEASE: 20261010-1852 cloudflare-control lease CLOSED by PARTIAL finding; recheck fresh leases before deploy.
NEXT: recover authenticated noninteractive administrative command channel; deploy exact v16 after owner/lease check and independently verify /health; keep publisher fail-closed until version and flags match.
