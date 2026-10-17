# WordPress storage false blockage fixed in production
STATUS: PROVEN
AREA: wordpress-deploy
DATE: 2026-10-17
COMMITS: anthares-wordpress 38d6a97f9d0cb27306dd209cd4c4c0aa3bdc77de; anthares-clipper b12bb4468ae72d790657131d75e486165f4215dc
SUPERSEDES: test-hub/findings/20261017-1943-lease-wordpress-storage-accounting.md; test-hub/findings/20261017-1946-lease-cortes-storage-diagnostic.md
LEASES: CLOSED

## Root cause
Production video-storage.php imposed 20 GiB on ALL video files under main uploads, sandbox uploads and videos-para-cortar. Sandbox held approximately 26-28 GB of old unrelated site videos (e.g. platoao/andromaca categories), so empty CORTES directories could not clear the false blockage. Initial du main uploads 3934509091 bytes; sandbox 27747086983 bytes. Later observed video inventory changed independently during inspection; no media deletion performed by this correction.
The 14.7 GB interpretation in prior chat was false: log limit=***474836480 was GitHub-masked 21474836480 bytes, confirmed by deployed source. Do not treat masked decimal strings as literal numbers.

## Implemented
Hosting account quota explicitly configured to 100000000000 bytes, as owner's Hostinger panel shows. Account-wide allocated usage measured by du -s -B1 -x, never physical shared-host filesystem size as account quota. Keep 10000000000-byte safety margin; further constrain by filesystem free space; subtract serialized leases. Full account measurement cached for 60 sec, conservatively add observed positive video growth. Unknown quota, du error or disk-free measurement failure blocks.
CORTES-managed videos separated from sandbox and other inventory. bytes and limit_bytes remain compatible with the client preflight. Expose account_used_bytes, account_quota_bytes, safety_margin_bytes, available_bytes, all_video_bytes, other_video_bytes, inventory_groups and measurement_error.
Budget/status/cron never delete media; canonical CORTES lifecycle remains responsible for cleanup.
Client no longer claims a removed 20 GB fixed quota on HTTP 507.
GitLab source has older retention protections; read and preserve histories, no blind mirror performed.

## Deployment proof
Only wp-content/plugins/anthares-clipper/video-storage.php atomically replaced over configured SSH. Baseline expected SHA256 6cf4b52a7fa1260206a19df41d80cf0c903108962b39a196b12e57b4afbea661; new SHA256 6b33a12d54dbaba314167cc09f316802ce1d927dd04f9db6200be617a5429c2b. Backup and previous quota options saved under private account maintenance directory.
PHP lint PASS. 20 executable isolated PHP checks PASS. 32 focused Python regressions PASS; syntax/diff checks PASS.
Read-only preview against real account PASS before deployment.
Actual authenticated public HTTP /wp-json/anthares/v1/video-storage: status allowed=true; reserve 104857600 bytes PASS; concurrent accounting exactly +104857600 PASS; oversized 100000000000-byte reservation HTTP507 PASS; release PASS; final reserved_bytes=0, deleted=[] PASS.
Final policy hosting-account-headroom-v2; account_used_bytes=42467352576; quota=100000000000; margin=10000000000; available_bytes=47532647424; managed bytes=2521718252; sandbox video bytes=26367051975.
Temporary verification application password deleted; independent final count TEMP_VERIFICATION_CREDENTIALS=0.

## Limits
This proves the live storage blocker is corrected, not a successful complete CORTES production round. No new social post, media upload, deletion or daily workflow dispatch was performed. No capacity plan upgrade was purchased.
