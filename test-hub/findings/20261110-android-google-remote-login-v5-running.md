# Google Play login em Android remoto — versão interativa v5
STATUS: RUNNING
AREA: tiktok-live-cloud-google-remote-login
DATE: 2026-11-10
OWNER: chatgpt-tiktok-remote-login-v5
LEASE_AREA: tiktok-live-cloud-google-remote-login
LEASE_EXPIRES: 2026-11-10T23:45:00Z
RUN: pending
JOB: pending
BASELINE_PROVEN: Android 35 Google Play x86_64 boots on GitHub Actions (42872343720), Google Play requests Google login before TikTok install. Earlier tiktok-android-interactive-login-v4 39721664367 booted but GUI failed because Ubuntu scrcpy 1.25 incompatible with Android. HLS and virtual camera tests remain green, no LIVE control on web.
FAILED_AVOIDED: Replace scrcpy 1.25 with pinned official static scrcpy 3.3.4 SHA-256; no screen content in logs, no plaintext tunnel credentials in public GitHub repo. Do not touch PC/Android devices or Kwai publisher. Do not bypass Google verification.
SUCCESS_SIGNAL: GitHub-hosted Android35 with current scrcpy version, noVNC via Cloudflare tunnel protected by randomly generated strong password; HTTP401 without auth and HTTP200 with auth; encrypted RSA-OAEP URL/login credentials posted only as ciphertext in public PR comment, decrypted privately by assistant then delivered to user.
FAILURE_SIGNAL: runner KVM missing, AVD boot fails, scrcpy incompatible, tunnel unreachable or access check fails. Exact stage emitted, without exposing access secrets.
TEST_VALIDITY: User signs in directly with their Google account through protected remote Android interface, on their instruction. Never collect Google account password, 2FA, cookies, or print screenshots. Ephemeral runner is destroyed at job end; a durable state-save must be separately validated before calling account login persistent.
