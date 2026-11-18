STATUS: PARTIAL
DATE: 2026-11-18
OWNER: ChatGPT / CURSO ESCRITA CRIATIVA
JOB: studio-g6-parity-qa-20261118
LEASE: CLOSED
CODE: https://github.com/UniversoAnthares/anthares-wordpress/pull/322
BASE: PR #321 SHA ac0e9b1e384a06fc1a861802fdc1c647e7cdead7
FINAL_HEAD: fe49a3fefbc803aca362eba0cf82d6c59268c49e
SCOPE: Three changed files. JS removes Lixeira only from global sidebar and preserves project-context trash route. Navigation tests require all 14 original actions plus four extensions. CSS test correctly normalizes article#post-21383 -> article#post-19344.
EVIDENCE: Initial isolated checkout 90 tests / 2 FAIL (global Lixeira and invalid CSS normalization). Final isolated checkout of exact HEAD fe49a3f: 90/90 Python unittest PASS on Hostinger; manifesto QA 676/676 PASS, PHP 8.3 lint PASS, orchestrator QA 11/11 PASS.
NOTE: Original legacy plugin untouched. Production Studio already displays five menu items; this PR reconciles the stale GitHub branch. No production mutations.
PENDING: Browser click-by-click authenticated, live REST writes, screenshot comparison desktop/mobile, protected release coordination. Keep PR draft until gates.
CLEANUP: SSH ephemeral test checkout used trap for removal. No Windows files created.
