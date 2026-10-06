# Kwai READY-started-commit boundary executable proven
STATUS: PROVEN
AREA: kwai
DATE: 2026-10-05
RUN: https://github.com/UniversoAnthares/anthares-kwai-runner/actions/runs/37401137540
COMMIT: 7f22e31f372ba8526a1745da1c68e28312f3e675
SUPERSEDES: test-hub/findings/20261005-2150-lease-kwai-started-commit-boundary.md
LEASE_AREA: kwai-publish
LEASE_CLOSED: 2026-10-06T01:50:15Z

## Resultado
Item 2 orchestration is PROVEN behaviorally against the real kwai_publish.sh with Android/network/controller stubs.
- prepare emits READY before any central started call;
- rejected started ACK exits 86 and commit is never invoked;
- accepted started ACK precedes exactly one commit;
- commit failure after ACK invokes central fail/UNCERTAIN path;
- successful commit proceeds to specific verification and complete;
- source-order assertion independently enforces started before commit.

This complements the production-v16 control proof and the real publisher heartbeat wiring proof. Remaining Android proof is a runtime acceptance, not an orchestration implementation gap.
