# RUNNING — TikTok single canary media selection
STATUS: RUNNING
AREA: tiktok-canary-media
DATE: 2026-10-05
OWNER: CHAT 5

BASELINE:
- Render direct publisher preflight is PRODUCTION PROVEN.
- Central queue/dedupe is healthy; confirmed TikTok count today=0.
- No TikTok canary/publish lease newer than the closed earlier publish-hardening work was found before acquisition.
- Account-specific source ledger is empty, so selection must come from owned stream transcript evidence.

HYPOTHESIS:
The recent owned stream `a4w8KAOxANc` contains at least one continuous 30–90 second passage with a complete analytical idea suitable for a single TikTok canary.

SUCCESS_SIGNAL:
Obtain subtitle/transcript timestamps, identify up to 3 continuous candidates, and select exactly one passage whose beginning is immediately intelligible, body contains substantive literary analysis, and end completes the thought.

FAILURE_SIGNAL:
Subtitles unavailable, transcript unusable, or no complete candidate. In that case test the next discovered owned source without creating a queue job.

SAFETY:
Analysis only. No media upload to TikTok, no central enqueue/lease/started mutation, and no Render publish endpoint call during this lease phase.
