# Shared test-hub protocol

Before changing or testing this project, read `test-hub/README.md` and the relevant files under `test-hub/findings/`.

Rules:
- Treat the hub as the shared source of truth across simultaneous chats/agents.
- Do not repeat a FAILED path unless the new test explicitly changes the recorded failure cause.
- Preserve PROVEN behavior unless a newer real test supersedes it.
- After every meaningful test, create a new append-only finding using the template in the hub.
- Never put credentials, secrets, cookies, tokens, or session payloads in the hub.
- A run that failed because the test harness itself was broken is not evidence that the tested hypothesis failed.
