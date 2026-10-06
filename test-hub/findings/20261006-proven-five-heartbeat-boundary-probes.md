# Five heartbeat boundary probes — PROVEN
STATUS: PROVEN
AREA: qa / kwai-heartbeat
DATE: 2026-10-06
RUN: 37402890021
JOBS: 112073812922 ; 112073813046 ; 112073813138 ; 112073813142 ; 112073813146
SUPERSEDES: test-hub/findings/20261006-lease-five-heartbeat-boundary-probes.md

Five concurrent independent cases all green:
- initial-deny-no-child: initial renew denial returns 49 and child never starts.
- missing-job: fail closed before execution.
- missing-generation: fail closed before execution.
- periodic-deny: initial renew succeeds, later renew denial returns 49 / lease-heartbeat-lost.
- child-zero: fast successful child preserves zero and performs exactly the initial renew.

No login/Android/media publication or production mutation.
