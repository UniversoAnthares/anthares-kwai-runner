# Item fixo 9 — Vercel Blob entrega alternativa, primeira migração comprovada
STATUS: PARTIAL
AREA: threads/cloud-delivery-media
DATE: 2026-10-29 UTC
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/40927803268 ; https://vercel.com/lucasyahn-6808/anthares-cortes-cloud-media-qa/D5KvEGXvspA1mLca6qC7JNpEs3fG
JOB: Github 123637871004 ; Vercel dpl_D5KvEGXvspA1mLca6qC7JNpEs3fG
COMMIT: 43f73e81e23649ec6b9d8d5e73ebd43038bb20db
SUPERSEDES: 20261029-item9-vercel-blob-media-delivery-lease.md
LEASE: CLOSED for PR #1915; ongoing quarantine remains independently controlled.

## BASELINE_PROVEN
Neon 2026-10-29 18:08 UTC: Threads 195 confirmed, 99 queued, 1 failed, 98 isolated MEDIA_HTTP_403 and one EDITORIAL_MISSING, cloud_primary_enabled=false. Codeberg inactive, GitHub main authority unchanged.

## SUCCESS_SIGNAL
- Existing Vercel Hobby team: new Blob store anthares-threads-media-relay linked to project anthares-cortes-cloud-media-qa. BLOB_READ_WRITE_TOKEN injected to the Vercel project only, not copied to WordPress, Windows, repository or logs.
- Source exact short_fOmihuHUT1M_g1_7868_7908.mp4, WordPress attachment 17104, ledger row QUEUED+ISOLATED. Blob import executed in Vercel cloud build (no Windows staging) at dpl_D5KvEGXvspA1mLca6qC7JNpEs3fG: source HTTP 200 and sha PASS bytes=2090126; Blob upload to https://izu4hsz4kmpqtwkl.public.blob.vercel-storage.com/threads/fOmihuHUT1M/g1-7868-7908-7355d6c5358f.mp4 ; Blob readback HTTP 200, SHA256 7355d6c5358fdd81a53c93bff17275259bb57f15e44cbe639f95639f0b5cef96 PASS.
- GitHub PR #1915 merged at 43f73e81: exact clip identity+SHA+URL pinned in config/threads-media-delivery-mirrors.json; tools/cortes_threads_cloud_media_delivery.mjs rejects wrong hash or canonical URL and untrusted Blob host; caller validates SHA through captionForClip, Neon still reserves against original WordPress source URL; Graph video_url may use exact verified alternate URL only for this clip.
- GitHub Actions CI #40927803268, job #123637871004 SUCCESS: 23 tests PASS, 0 failed, Node syntax checks. Prior failed CI #40927583763 identified duplicate regex escaping, corrected in commit 3746f275. Final real main push CI #40927966104 SUCCESS, THREADS_ALLOW_PUBLISH=0, THREADS_QUEUE_EMPTY_OR_ISOLATED. No social post triggered by this migration.
- Fixed list item 9 retains four recovery variants: A Vercel Blob active and proven for one object; B Hostinger subdomain independent CDN standby; C Cloudflare R2 standby; D Anthares Media Gateway standby as orchestration if needed. Other 10 fixed items unchanged.

## FAILED_AVOIDED
No mass migration, unknown video, secret movement, bypass of CDN security, unfenced social post, quarantined row release, Neon write or identity overwrite. Do not interpret CI green as a real Threads post or as clearance of other 97 MEDIA_HTTP_403 clips.

## NEXT ESSENTIAL STEP
Individually authenticate and verify one queued isolated clip by media SHA and editorial attestation, then use a legitimate reviewed/authorized quarantine-reconciliation mutation and fenced primary handoff. No direct destructive SQL without separate approval. After one actual post with remote permalink and ledger confirmation, expand transfers in quota-limited batches. Verify existing Vercel Hobby quota before 98-object transfer; leave B/C/D available as redundant routes.

## TEST_VALIDITY
SHA compared both before and after Blob upload in an independent Vercel environment; 23/23 hosted GitHub code tests; SHA/identity pinned. No real Graph publication and no production quarantine mutation; fixed item 9 remains PARTIAL.
