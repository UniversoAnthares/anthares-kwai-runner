# Fanout WordPress GET transient preflight repair

AREA: network fanout read-only preflight only. OWNER: ChatGPT task.
STATE: RUNNING. START: 2026-11-19T04:07:59.305Z. EXPIRES: 2026-11-19T04:36:59.305Z.
BASELINE: three-network fanout run 44445986386 failed in stage=wordpress with URLError before any queue write; prior run 44380625167 succeeded. HEAD 717f0f3ab4f03aaed89ca23cc59ed59d609fffde.
FAILED_AVOIDED: no replay of POST, no retry of HTTP 401/403/429 (HTTPError), no manual posts, no security bypass.
SUCCESS_SIGNAL: offline tests show one retry on transient URL transport and exactly zero retry for HTTP denial, existing fanout isolation contracts still pass; then production preflight can tolerate one network glitch.
FAILURE_SIGNAL: CI tests fail, source HEAD diverges or retry touches authenticated HTTP rejection.
TEST_VALIDITY: GitLab dual peer main stale/missing target code; no blind mirror; no active causal cloud jobs at observation.
