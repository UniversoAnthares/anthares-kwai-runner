# MEmu4 standby recovered and launcher autoheal corrected
STATUS: PARTIAL
AREA: kwai-login
DATE: 2026-11-22
SUPERSEDES: test-hub/findings/20261122-0848-lease-kwai-login-memu4-standby.md
RUN: Windows Task Scheduler Anthares-MEmu4-Recovery-Launcher at 2026-11-22 08:53:53 -04:00
COMMIT: none (existing approved local launcher in-place maintenance)
OWNER: ChatGPT on direct owner request

## Evidence
- Windows MEmu_4 headless PID 4704 in Lucas session 1; ADB port 5037, serial 127.0.0.1:21543; Android boot_completed=1 and com.kwai.video installed.
- Observed black screenshot with status bar, app process alive and mCurrentFocus=null. App-only force-stop and relaunch restored Kwai feed UI without VM reboot, logout, or app-data reset.
- Read-only profile UI (in-memory ADB XML, Android temp deleted after probe) exposed @lucasrosalem and Edit Profile, no login prompt. No posting performed.
- Maintained separate physical phone ADB 5038, serial 993fce720408; physical primary intact.
- Canonical local launcher C:\ProgramData\AntharesRemoteAgent\memu4-recovery-launcher.ps1 updated in-place; before SHA256 EA9E699740C2AAABC1BE0EF62C73DCF57B63A5028EFA74CCFD6AE599772EE560; after SHA256 EBEF11A7CAC23B5B481255DCE96F90DA3804F226F41BBBA9CF67FA677F340F07; PowerShell parser accepted.
- Existing scheduled task executed at 08:53:53 local, LastTaskResult=0, log: 'memu4 Android+Kwai UI ready; publisher must verify authenticated account before failover'.
- Launcher now verifies ADB + Android boot + Kwai package + active window focus before returning success; if black/unresponsive, app-only restart with guard against active publisher; fail-closed on unready state.
- Publisher config still intentionally requires authenticated identity verification before standby promotion; secondary enabled but never tested by interrupting physical primary.

## Assessment
PROVEN: restored Android UI, active logged-in @lucasrosalem profile, ready ADB on separate VM port, repaired launcher with successful actual scheduled task test.
UNVERIFIED: a real Kwai failover with publication receipt under physical-primary outage; no unsafe test posting.
Released kwai-login maintenance lease; standby remains conditioned on publisher identity check and single-writer protection.
