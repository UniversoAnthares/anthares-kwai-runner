# TikTok canary transcript — anonymous GitHub runner blocked by YouTube
STATUS: FAILED — source extraction before subtitles
AREA: tiktok-canary-media
DATE: 2026-10-05
OWNER: CHAT 5

RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37396595992
JOB: 112053951188
SOURCE: https://www.youtube.com/watch?v=a4w8KAOxANc

OBSERVED:
- `yt-dlp --list-subs` and subtitle-only extraction reached YouTube but were rejected with `Sign in to confirm you’re not a bot`.
- No video/media was downloaded.
- Ranking step never ran.
- yt-dlp also warned that no supported JavaScript runtime was available on that hosted runner.

CLASSIFICATION:
This is a YouTube extraction/authentication/IP path failure, not evidence that the owned source lacks subtitles.

NEXT_CAUSAL_TEST:
Stay cloud-only. Install Deno on the hosted runner and test subtitle-only extraction through a small matrix of supported YouTube player clients (`android_vr`, `tv_embedded`, `web_safari`, default with Deno). Stop on the first client that yields a VTT. Keep video download and TikTok queue mutation disabled.
