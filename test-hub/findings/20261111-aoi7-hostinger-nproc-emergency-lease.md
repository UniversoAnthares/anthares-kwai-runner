# AOI #7 — Hostinger NPROC saturation and 24h emergency boost
STATUS: RUNNING
AREA: architecture/forgejo-daemon-hostinger-resource-exhaustion
OWNER: chatgpt-aoi7-hostinger-nproc-20261111
DATE_UTC: 2026-11-11T12:18Z
BRANCH: ops/forgejo-nproc-hostinger-20261111
BASE_SHA: ee6b4d9eafe288b5dd1e55a6798467c6475a931e
SUPERSEDES: 20261111-forgejo-hpanel-daemon-recovery-proven.md
BASELINE_PROVEN: Hostinger Cron Jobs still lists one */5 forgejo_keepalive.sh and unchanged mirror jobs (17 hourly and 0,30 half-hour). Prior real Hostinger keepalive stdout FORGEJO_KEEPALIVE_RECOVERED=PASS pid=2880553. Recent mirror-job View Output said "flock: fork failed: Resource temporarily unavailable". Keepalive output was blank on a fresh panel reload; after switching dialogs the same error string appeared, so keepalive-specific attribution is unproven. Resource Usage showed NPROC limit 80 reached repeatedly, with PHP workers and memory normally below limits. Owner-authenticated hPanel shows zero-cost 24h increase to Business capacity with NPROC from 80 to 120, activated around 2026-11-11T12:09Z (local America/Campo_Grande 08:09). Confirmed banner "O aumento de recursos está ativado" and remaining 23h53 at 12:15Z, cap chart "Limite 120". From local 08:10 to 08:17 the NPROC count was 59-82, below 120.
FAILED_AVOIDED: never run bulk "Parar processos em execução", never change mirror/media schedules, never bypass the explicit Hostinger remote executor denial, never incur a paid upgrade; preserve running Forgejo and other services.
SUCCESS_SIGNAL: append a truthful resource-limitation incident record and distinguish 24h temporary capacity from permanent AOI completion.
FAILURE_SIGNAL: missing evidence of cap 120 or incorrect attribution of a blank keepalive cron output.
TEST_VALIDITY: authenticated hPanel UI readback, known existing cron row; public HTTPS/origin and actual process inventory remain out of scope due previous security denial.
NO_ADDITIONAL_COST: true
SOCIAL_POSTS: 0
