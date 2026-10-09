# Live ACTION_SEND test in hosted Android after proven cloud install
STATUS: RUNNING
AREA: kwai-cloud-android-share-intent-smoke
DATE: 2026-10-09
OWNER: chatgpt-kwai-cloud-share
LEASE_UNTIL: 2026-10-09T23:59:00Z
HEAD_BASELINE: 594a517402beb6aed5f43e0bfb3d291351374eef
RESOURCES: .github/workflows/kwai-agent-cloud-install.yml (only)
BASELINE_PROVEN: hosted run 37965500823 success, Kwai installed and launched, Anthares Agent installed/foreground, FileProvider present, Kwai manifest declares SEND video MIME. No authenticated session or video transfer proof.
FAILED_AVOIDED: run 37964764063 lacked checkout; run 37965097557 lacked adb PATH. Both corrected. No repeating those failure modes. Do not use local PC or account secrets; no publication; do not assume manifest intent handler means editor accepts a video.
SUCCESS_SIGNAL: hosted runner creates a harmless local 1-second video, imports into Android MediaStore, issues Android ACTION_SEND video/mp4 to official Kwai, checks activity target and records sanitized result (no screenshots/DOM).
FAILURE_SIGNAL: media scanner unavailable, Android intent not resolved, target app rejects launch, or remains at login wall. Report precise stage.
TEST_VALIDITY: cloud Android is ephemeral and not authenticated; even a share editor opening is not a post.
PEER: GitLab main missing workflow path, no blind mirror.
