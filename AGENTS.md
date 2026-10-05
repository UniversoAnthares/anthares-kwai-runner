# Shared test-hub protocol

Before ANY change or test in this project, the agent MUST perform the hub preflight below. Reading only README is not sufficient.

## Mandatory preflight
1. Read `test-hub/README.md`.
2. List `test-hub/findings/` and read ALL findings newer than the last consolidated timestamp in README for the same area/causal chain, plus every finding explicitly referenced by them through SUPERSEDES/baseline.
3. Check current GitHub Actions runs for the same causal chain. Do not launch a competing experiment while a causally relevant RUNNING test exists, unless the new test is explicitly an independent layer.
4. Before creating a run, write its RUNNING finding first (or in the same change set) with:
   - BASELINE_PROVEN
   - FAILED_AVOIDED
   - SUCCESS_SIGNAL
   - FAILURE_SIGNAL
   - TEST_VALIDITY
5. A matrix may branch only AFTER every variant reaches the same observable precondition. If a job does not reach that precondition, classify it INVALID/NOT_TESTED, never as hypothesis FAILED.
6. A green GitHub job is not PROVEN unless its declared SUCCESS_SIGNAL appears in evidence.
7. After completion, append a new finding and SUPERSEDE the RUNNING finding. Update README consolidated state when the causal conclusion changes.

## Preservation rules
- Treat the hub as the shared source of truth across simultaneous chats/agents.
- Do not repeat a FAILED path unless the new test explicitly changes the recorded failure cause.
- Preserve PROVEN behavior unless newer real evidence supersedes it.
- Never put credentials, secrets, cookies, tokens, or session payloads in the hub.
- Harness failure is not evidence that the tested hypothesis failed.
- Do not infer success/failure from workflow conclusion alone; inspect decisive logs/artifacts.
