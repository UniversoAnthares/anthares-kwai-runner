# Test Hub write protocol

Canonical summary: ../TEST-HUB.md

## Append-only evidence records

For every meaningful real test, add one file under:

    test-hub/results/<run-id>-<short-component>.md

Use the GitHub run ID whenever one exists. This prevents simultaneous chats from editing the same ledger file.

Required fields:

    # <run-id> — <component>
    Date:
    Scope:
    Result: PASS REAL | PASS TÉCNICO | FAIL CONHECIDO | PENDENTE
    What was actually tested:
    Evidence:
    Failure layer:
    Root cause:
    Change made:
    Do not repeat:
    Next valid test:

Rules:
- Never include secrets, cookies, session material, private screenshots, passwords or tokens.
- Do not overwrite another run record.
- A green CI job is only PASS REAL if it directly proves the final external behavior.
- Update ../TEST-HUB.md only when the canonical current state or a consolidated decision changes.
- If simultaneous edits conflict on TEST-HUB.md, re-read HEAD, merge facts, then retry. Never discard another chat's new evidence.
