# Lease: YouTube Shorts WordPress claim HTTPError repair
STATUS: RUNNING
AREA: queue
DATE: 2026-11-22
START: 2026-11-22T08:40:00-04:00
EXPIRES: 2026-11-22T09:10:00-04:00
OWNER: ChatGPT on direct owner instruction
BASELINE: anthares-clipper main d2459e4e72091de22e28a80a95d8b48d899b9e; scheduled Shorts run 44944591374 failed before upload with YOUTUBE_ATOMIC_CLAIM_SERVICE_UNAVAILABLE, 3 HTTPError; YouTube channel verified, 854 editorial candidates, zero uploads.
CONCURRENT: check fresh workflow runs and refs before mutation; preserve all immutable WP claims and uncertain remote outcomes.
HYPOTHESIS: wp_post emits requests.exceptions.HTTPError, but cloud catches urllib.error.HTTPError only; HTTP 409 incorrectly opens circuit.
PLAN: handle numeric 409 from requests and urllib; safe status diagnostics; regression test; deploy only via reviewed branch and CI.
FAILED AVOIDED: no blind duplicate upload, no bypass of WordPress, no unverified change of identity or secrets.
SUCCESS: targeted test passes; live workflow handles 409 safely or reveals real HTTP status.
CLOSURE: append result finding before expiry.