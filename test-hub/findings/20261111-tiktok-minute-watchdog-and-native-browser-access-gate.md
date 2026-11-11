# TikTok Restream minute watchdog and native browser LIVE access gate
STATUS: PARTIAL
AREA: tiktok-live-native-and-continuity
DATE: 2026-11-11
PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2301
SUPERSEDES: none
BASELINE_PROVEN: TikTok Restream host supervisor active on Hostinger, public video and audio already proven, Kwai parallel but independent
FAILED_AVOIDED: never modify Kwai Cron as an unproven scheduler, never use owner's Windows interactive mouse/keyboard, never claim official TikTok LIVE access or hPanel Cron without actual authorization
SUCCESS_SIGNAL: repeated one-minute independent watchdog receipts with live enabled, supervised FFmpeg alive, and actual TikTok browser native LIVE control rendered under existing authenticated state
FAILURE_SIGNAL: watchdog loop unavailable, TikTok LIVE no video, native Live Producer redirects to non-broadcast page
TEST_VALIDITY: independent SSH readback and GitHub-runner browser with account's stored auth state, no external retransmission started

## Item 2: minute recovery watchdog
- Existing Hostinger hPanel administrative credential and Hostinger API token were not available in GitHub/GitLab connected sources. The shared-host SSH environment has no crontab command. The Forgejo existing cron bridge last recorded successful activity on November 5, and the Kwai source-refresh timestamp was unchanged through the native cron investigation. As a result, neither was treated as an established recurring scheduler and neither was modified.
- A low-resource independent watch loop was added to `/home/u566597497/.anthares-tiktok-restream/supervisor.sh`, command `watchdog-loop`, using `setsid -f` and `flock`. Every 60 seconds it runs `timeout 20 bash supervisor.sh tick`; tick stops when disabled and respects the circuit breaker. Neither watchdog can touch Kwai PIDs/paths.
- Source commit: `8be64b21a38d1564bf4674e749fda94cc3453b63`. Initial watchdog PID bug (literal '$') was corrected by `e60d052a25710222ec834ece2e0550a9ab0c8b97`. Deployed via https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43037949915.
- After ending only old watchdog-loop PID 3265792, the new detached loop reported numeric PID 3342879. Host readback confirmed `watchdog-last-tick` at 2026-11-11T14:26:05Z, 14:27:05Z, and 14:31:06Z, while `TIKTOK_HOSTINGER_SUPERVISOR=RUNNING`, `TIKTOK_HOSTINGER_FFMPEG=RUNNING` and `TIKTOK_HOSTINGER_ENABLED=1`.
- An independent public TikTok spectator browser reported `Lucas Rosalem (@lucasrosalem4) is LIVE - TikTok LIVE`, video `readyState=4` and playing, 1280x720, with one audio track, after the watchdog was installed.
- FUNCTIONAL: one-minute checks operate while the detached loop remains alive. hPanel Cron scheduled entry has NOT been created, and recovery after both supervisor and watchdog are terminated remains dependent on previously configured external monitoring. Do not mark persistent native hPanel Cron job as complete.
- Official exact hPanel Cron once admin token/session available: type Custom, schedule `* * * * *`, command `/bin/bash /home/u566597497/.anthares-tiktok-restream/supervisor.sh tick`. The Hostinger API documented POST /api/hosting/v1/accounts/u566597497/cron-jobs with JSON `{"time":"* * * * *","command":"/bin/bash /home/u566597497/.anthares-tiktok-restream/supervisor.sh tick"}`. Never expose bearer token.

## Item 3: native TikTok LIVE
- Existing authenticated TikTok state for @lucasrosalem4 was loaded in isolated GitHub Ubuntu cloud Chromium. No local desktop browser, window, input events, or audio devices were used.
- Read-only test of `https://livecenter.tiktok.com/producer` redirected to `/`; no `Go LIVE`, camera/virtual-camera, or practice control. Main livecenter root also had no such controls. `https://www.tiktok.com/tiktokstudio` rendered ~58 controls but no native browser Go LIVE button. `https://www.tiktok.com/tiktokstudio/live` returned empty shell. Seller Center redirected to account registration. This was verified with cloud GitHub run https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43039224201 (job 130586327294, SUCCESS).
- Fake cloud camera and microphone worked separately in Chromium (video=1, audio=1, 640x480), but this did not enable TikTok's native broadcaster.
- Official `https://www.tiktok.com/studio/download` requirements as displayed to browser include Windows x64 10+, DirectX 11, >=8GiB RAM and NVIDIA GTX 10 series or AMD Radeon graphics. Existing free Windows cloud runner tested in https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43027322351 has 16GiB memory but only a basic virtual GPU and fails the vendor GPU gate. A real native TikTok LIVE Studio session was not launched.
- Earlier attempt https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43037794426 was cancelled during slow Chromium install. Causal change switched to preinstalled Google Chrome and the subsequent run passed. Never claim previous cancelled attempt demonstrated account denial.
- Native LIVE remains technically blocked by missing eligible browser route and missing graphics-compatible persistent desktop host; platform permission and prerecorded programming authenticity policy are separate prerequisites. Do not attempt to spoof an approved creator or bypass LIVE eligibility.
