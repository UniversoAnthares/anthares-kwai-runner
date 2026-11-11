# TikTok Restream Hostinger six-hour rolling LIVE - running
DATE: 2026-11-11
STATUS: RUNNING (first six-hour completion and automatic renewal not yet proven)
AREA: tiktok-live-restream-hostinger-6h
OWNER: chatgpt-anthares-tiktok-20261111
ROOT: /home/u566597497/.anthares-tiktok-restream
LEASE_AREA: tiktok-live-restream-hostinger-6h
LEASE_EXPIRES: 2026-11-12T01:00:00Z
REPO_BRANCH: feature/tiktok-live-authorized-cloud-20261110
PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2301

## Evidence
- Existing Hostinger FFmpeg static binary and local Kwai HLS VOD were verified available. Local HLS index has 3785 segments, H264 1280x720 30fps, ffprobe format duration 22716.424212 seconds (> six hours).
- Heavy 720x1280 re-encoding with libx264 was refused by Hostinger (`Error while opening decoder: Resource temporarily unavailable`); never forced that path or touched Kwai process. Local video-copy plus AAC resampling test succeeded in remote Actions job https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43017772582.
- Separate Hostinger supervisor source `tools/tiktok_restream_hostinger_supervisor.sh` was deployed via authenticated GitLab SSH bridge in https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43018593081. Folder .anthares-tiktok-restream, independent of .anthares-kw12. Uses `nice -n 15`, original H264 video copy, AAC audio, local VOD playlist, 21600 second FFmpeg cycle, duplicate lock, crash-retry limiter (3 strikes disables), and log/progress files. Ingest key supplied only through GitHub secret at bootstrap and stored mode 600.
- Manual activation of host supervisor via Github Actions `action=start` completed SUCCESS: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43018768837. Status at 2026-11-11T12:15:44Z: TIKTOK_HOSTINGER_SUPERVISOR=RUNNING, TIKTOK_HOSTINGER_FFMPEG=RUNNING, TIKTOK_HOSTINGER_ENABLED=1.
- Hostinger read-only status at ~12:17Z showed `2026-11-11T12:15:40Z CYCLE_STARTED`, FFmpeg progress `out_time_ms=90989889`, two FFmpeg processes (approximately 3.2% and 3.3% CPU; RSS ~39-40MiB) and no change to Kwai scripts.
- Independent public browser viewer https://www.tiktok.com/@lucasrosalem4/live: LIVE title presented, visible decoded footage in public screenshot (landscape video with TikTok margins), media element readyState=4, playing=true, 1280x720. Audio confirmed using WebAudio RMS 0.06218, without login. The prerecorded nature is disclosed by Restream TikTok title `ANTHARES | PROGRAMA GRAVADO`.
- Recurring hourly condition-watch monitor created for Hostinger supervisor and public LIVE. It may restart unexpected crash only while enabled=true; circuit breaker or authorization errors remain disabled.

## Limitations
- An actual six-hour completed cycle, next-cycle automatic renewal and week-long uptime have not yet occurred; leave this finding RUNNING until independently observed. Expected first six-hour boundary from 2026-11-11T12:15:40Z is around 18:15:40Z; account for clock jitter and FFmpeg progress.
- Restream help: as of July 2025, third-party TikTok LIVE eligibility requires at least 50% gaming content to maintain access. Literary programming may cause third-party eligibility to be revoked. https://support.restream.io/en/articles/6721574-stream-to-tiktok
- Hostinger support says resource-heavy FFmpeg is officially supported on VPS, while this existing account already runs a Kwai FFmpeg. A second, copy-only process may still be throttled by resource limits. https://support.hostinger.com/pt/articles/1583239-o-ffmpeg-e-compativel-com-a-hostinger
- No guarantee that TikTok or Restream will allow indefinitely continuous prerecorded LIVE. Any policy rejection is a stop condition, never bypass.
- GitHub feature branch not merged; safe deploy and manual control available through repository workflow on branch. Hostinger supervisor does not need Actions runner to remain active.

## Criteria to close
1. First six-hour cycle completes successfully with `CYCLE_COMPLETED` in host supervisor log.
2. New `CYCLE_STARTED` appears automatically a few seconds after cycle 1 without manual dispatch.
3. Independent public TikTok viewer proves video and audio during cycle 2, while Kwai remains operational.
4. If failed, use hourly monitor receipts and update or stop the independent TikTok supervisor only.