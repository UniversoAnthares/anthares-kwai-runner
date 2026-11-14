# TikTok LIVE via Restream – 120-second cloud publishing experiment
DATE: 2026-11-11
STATUS: PARTIAL
AREA: tiktok-live-restream-ingest
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43003962453
JOB: 130466714379
PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2301

## Validated operational evidence
- Authenticated Restream dashboard showed one of two channels enabled: TikTok Lucas Rosalem ON; YouTube Universo Anthares OFF. An encoder stream was configured in the Restream event, with RTMP URL `rtmp://live.restream.io/live` and a masked stream key.
- Stream key transferred directly into GitHub Actions secret `RESTREAM_ENCODER_RTMP_DESTINATION`, then the secret name was confirmed; secret value never printed or added to files.
- GitHub workflow `tiktok-restream-cloud-canary.yml`, dispatched with `transmit=true` and `seconds=120` on feature branch. Runner was GitHub hosted Ubuntu, no personal Windows or Android used to encode or push video.
- HLS source: https://anthares.us/wp-content/uploads/anthares-live-static/live.m3u8 (the Kwai source). Runner log: `ANTHARES_HLS_PREFLIGHT_OK=1` and `ANTHARES_DRY_ENCODE_OK=1`.
- RTMP transmission step completed with `FFMPEG_PROCESS_COMPLETED=1` logged at 2026-11-11T10:31:39.6514391Z; complete GitHub job conclusion SUCCESS. Start of transmission step HLS preflight marker 2026-11-11T10:29:35.6358267Z.
- During that two-minute period a separate public Chromium browser loaded `https://www.tiktok.com/@lucasrosalem4/live` (HTTP 200) and reported page title `Lucas Rosalem (@lucasrosalem4) is LIVE - TikTok LIVE`. After the FFmpeg job completed, the public page title was empty. An unrelated ordinary TikTok profile `/@openai/live` showed `No LIVE` and an empty title.

## What the evidence proves and does not prove
- PROVEN: cloud FFmpeg finished an actual 120-second transmission step using the captured Restream encoder destination. Public TikTok page independently presented a LIVE state during the push.
- NOT YET PROVEN: visual confirmation of decoded Anthares video frames/audio by a separate spectator; target stream category/title correctness; sustained operation beyond a 2-minute canary; recurring 6h schedule; TikTok platform continuing authorization for non-gaming prerecorded programming.
- No change was made to existing Kwai broadcast workflow. YouTube channel was disabled in Restream throughout the screenshots.
- The Restream event still displayed an old channel title `Tinha um POLVO no ELEVADOR`; correct title to explicitly say `PROGRAMA GRAVADO` before any long-running public transmission.

## Next completion criteria
1. Update TikTok Restream event title and channel topic accurately. The broadcast itself overlays `PROGRAMA GRAVADO`.
2. Run a longer 10-minute canary and obtain independent spectator video/audio evidence.
3. Verify TikTok LIVE policies and limits (third-party access and possible maximum session duration) before enabling a cycle scheduler.
4. Select persistent FFmpeg host separate from the user's PC/Android; keep Twitch/YouTube and Kwai unchanged.