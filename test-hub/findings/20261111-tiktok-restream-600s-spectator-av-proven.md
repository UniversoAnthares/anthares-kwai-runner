# TikTok LIVE via Restream - 600s cloud stream and independent viewer evidence
STATUS: PROVEN_600S_AV_TEST / RECURRING_DISABLED
AREA: tiktok-live-restream-ingest
DATE: 2026-11-11
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/43009188747
JOB: 130484191941
PR: https://github.com/UniversoAnthares/anthares-kwai-runner/pull/2301

## Evidencia operacional
- Evento Restream e canal TikTok (@lucasrosalem4, Lucas Rosalem) editados, readback: ANTHARES | PROGRAMA GRAVADO. Titulo antigo mantido no canal YouTube, mas esse canal foi mantido OFF. Conta TikTok unica habilitada na lista Restream.
- GitHub hosted Ubuntu FFmpeg: HLS Kwai Anthares preflight and 8s local transcoding passed. Manual dispatch with transmit=true, seconds=600.
- Log markers: 2026-11-11T11:07:13.4659827Z ANTHARES_HLS_PREFLIGHT_OK=1 on send step; 2026-11-11T11:17:18.8862182Z FFMPEG_PROCESS_COMPLETED=1. Job completed SUCCESS.
- Independently launched public browser (no login) at https://www.tiktok.com/@lucasrosalem4/live. During push, TikTok page title: Lucas Rosalem (@lucasrosalem4) is LIVE - TikTok LIVE. Public screenshot visibly showed program frames and PROGRAMA GRAVADO disclosure. DOM video: 720x1280, readyState=4, paused=false, currentTime advanced from 5.1 to 8.37 seconds.
- Public player audio: captureStream.getAudioTracks() yielded one live, enabled, unmuted audio track. After unmuting, WebAudio AudioContext analyser over ~3.6s showed nonzero RMS max ~0.051118, demonstrating audible signal in viewer session.
- After FFmpeg stopped, authorized Restream dashboard showed encoder OFFLINE, TikTok channel Off-line, YouTube Off-line. TikTok public title briefly continued displaying 'is LIVE' without a <video> DOM element; platform-side termination propagation not independently confirmed at the same instant.

## Status / limits
- PROVEN: completed 600-second encode and RTMP transmission; video frames and nonzero audio received through public TikTok player while broadcasting; Restream OFFLINE after input stopped.
- NOT PROVEN: continuous 6h cycles; durable FFmpeg host allocation; 24h automation safety; future platform authorization on non-gaming literature content.
- Restream official TikTok help documents since 2025-07-07 a 50% gaming content criterion for continued third-party LIVE access. Source: https://support.restream.io/en/articles/6721574-stream-to-tiktok
- Restream duration policy: TikTok no platform limit, restart continuous Restream connection every 24h. https://support.restream.io/en/articles/9096867-how-long-can-i-stream-for
- TikTok Shop (specifically commerce LIVEs) content rules warn against prerecorded streams and looping media; coverage for ordinary literary LIVE account is not established from those commerce rules. Source: https://seller-sg.tiktok.com/university/essay?from=policy&identity=1&knowledge_id=7651420422211329&role=2
- Recurring cycles are intentionally DISABLED due risk of account losing third-party LIVE access and large paid/free CI minutes for 24/7 FFmpeg. The tested manual canary remains available. No modifications to Kwai broadcaster.

## Next gate
Before enabling unattended 6h prerecorded streams, confirm TikTok LIVE account can retain authorization for the specific non-gaming recorded format, identify compliant program format, and host continuous FFmpeg without exhausting GitHub Actions quotas. Preserve disclosed prerecorded labels.